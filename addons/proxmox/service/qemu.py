import logging
import time
from typing import Any, Dict, List
from uuid import uuid4

from proxmox.enums.qemu import QemuStatus
from proxmox.enums.status import StatusCode
from proxmoxer.core import ResourceException

_logger = logging.getLogger(__name__)

class QemuAgentManagement():

    def __init__(self, connection):
        self._proxmoxer  = connection

    """Manages QEMU agent operations."""

    def get_qemu_agent_status(self, node: str, vmid: str) -> Dict[str, Any]:
        """Get the status of the QEMU agent on a VM."""
        try:
            self._proxmoxer.nodes(node).qemu(vmid).agent.post('ping')
            return {"status": QemuStatus.running}
        except ResourceException as e:
            return {"status": QemuStatus.pending}
        except Exception as e:
            return {
                'status': QemuStatus.failure,
                'exception': e
            }
    
    def ping_qemu(self, node: str, vmid: int, **kwargs) -> List[Dict[str, Any]]:
        """Ping QEMU agent for a specific VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).agent.ping.post()
    
    def get_memory_blocks(self, node: str, vmid: int, **kwargs) -> List[Dict[str, Any]]:
        """Ping QEMU agent for a specific VM."""
        return self._proxmoxer.nodes(node).qemu(vmid).agent.get('get-memory-blocks')

    def get_exec_status(self, node, vmid, pid):
        """Get the status of a command execution."""
        try:
            response = self._proxmoxer.nodes(node).qemu(vmid).agent('exec-status').get(pid=pid)
            return {
                'status_code': StatusCode.sucess,
                'msg': response
            }
        except ResourceException as e:
            return {
                'status_code': StatusCode.failure,
                'error_msg': str(e)
            }
        except Exception as e:
            return {
                'status_code': StatusCode.failure,
                'error_msg': str(e)
            }


#######################
# MARK: QEMU Agent Management
#######################

    def execute_shell_script(self, script_content: str, node: str, vmid: str):
        """Execute a shell script on the VM using QEMU guest agent"""
        _logger.info(f"Executing shell script on VM {vmid}")
        # Replace script name with a uuid, to make sure it is uniqe
        script_path = f"/tmp/proxmox_script_{uuid4()}.sh"
    
        try:
            # Use the correct file-write endpoint with proper parameters
            self._proxmoxer.nodes(node).qemu(vmid).agent("file-write").post(
                content=script_content,
                file=script_path,
                encode=1
            )
        
            # Make the script executable
            # For the exec endpoint, command should be an array of strings
            chmod_res = self._proxmoxer.nodes(node).qemu(vmid).agent("exec").post(
                command=["chmod", "+x", script_path]
            )
            
            # Wait for chmod to complete
            chmod_status = self._proxmoxer.nodes(node).qemu(vmid).agent("exec-status").get(
                pid=chmod_res.get('pid')
            )
            
            # Check if chmod was successful
            if chmod_status.get('exitcode', 1) != 0:
                raise Exception(f"Failed to make script executable: {chmod_status.get('err-data', '')}")
        
            # Execute the script with sudo
            exec_res = self._proxmoxer.nodes(node).qemu(vmid).agent("exec").post(
                command=["sudo", script_path]
            )
            
            # Poll for completion
            exec_result = None
            while True:
                exec_status = self._proxmoxer.nodes(node).qemu(vmid).agent("exec-status").get(
                    pid=exec_res.get('pid')
                )
                
                # Check if command has exited
                if exec_status.get('exited', False):
                    exec_result = exec_status
                    break
                
                # Wait before polling again
                time.sleep(1)
        
            # Parse the execution result
            stdout = exec_result.get('out-data', '')
            stderr = exec_result.get('err-data', '')
            exit_code = exec_result.get('exitcode', 1)
        
            status = "success" if exit_code == 0 else "failed"
        
            results = {
                "exec_result": exec_result,
                "status": status,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code
            }
        
            # Clean up the script
            cleanup_res = self._proxmoxer.nodes(node).qemu(vmid).agent("exec").post(
                command=["rm", script_path]
            )
            
            # Wait for cleanup to complete
            self._proxmoxer.nodes(node).qemu(vmid).agent("exec-status").get(
                pid=cleanup_res.get('pid')
            )
        
            return results
        
        except Exception as e:
            _logger.error(f"Failed to execute script on VM {vmid}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }


    def execute_command(self, node: str, vmid: str, command: str) -> Dict[str, Any]:
        """
        Execute a command on a VM using the QEMU agent.
        
        NOTE: To execute a sell command the command argument should start with `/bin/sh -c "echo test > /test.file"`
        See: https://forum.proxmox.com/threads/how-to-create-or-edit-file-with-qm-guest-agent.89759/

        Args:
            node: Node name
            vmid: VM ID
            command: Command to execute
            
        Returns:
            Command execution response
        """
        response = self._proxmoxer.nodes(node).qemu(vmid).agent('exec').post(command=command)
        return response
    
    def await_qemu_agent_ready(self, node: str, vmid: str, timeout: int = 300, interval: int = 5) -> bool:
        """
        Waits for the QEMU agent to be ready.
        
        Args:
            node: Node name
            vmid: Virtual machine ID
            timeout: Maximum time in seconds to wait for the agent to be ready
            interval: Time in seconds between each status check
            
        Returns:
            True if the agent is ready, False if it timed out or encountered an error
        """
        elapsed_time = 0

        while elapsed_time < timeout:
            res = self.get_qemu_agent_status(node, vmid)
            
            if res["status"] == QemuStatus.running:
                return QemuStatus.running
            
            if res["status"] == QemuStatus.failure:
                raise ValueError(res["exception"])

            time.sleep(interval)
            elapsed_time += interval

        _logger.warning(f"Timeout waiting for QEMU agent on VM {vmid}")
        return QemuStatus.failure

    def get_qemu_agent_status(self, node: str, vmid: str) -> Dict[str, Any]:
        try:
            self._proxmoxer.nodes(node).qemu(vmid).agent.post('ping')
            return {"status" : QemuStatus.running}
        except ResourceException as e:
            return {"status" : QemuStatus.pending}
        except Exception as e:
            return {
                'status': QemuStatus.failure,
                'exception' : e
            }
        
    def get_qemu_agent_info(self, node: str, vmid: str) -> Dict[str, Any]:
        try:
            res = self._proxmoxer.nodes(node).qemu(vmid).agent.get('info')
            return res
        except Exception as e:
            return {
                'status': QemuStatus.failure,
                'exception' : e
            }
        
    def check_vm_ready(self, node, vmid):
        result = {
            "ready": False,
            "agent_running": False,
            "message": "Unknown status"
        }
        
        try:
            # Step 1: Check if the agent is responding to ping
            try:
                self._proxmoxer.nodes(node).qemu(vmid).agent.ping.post()
                result["agent_running"] = True
            except Exception as ping_error:
                return {
                    'status': QemuStatus.failure,
                    'exception' : ping_error
                }
                
            # Step 2: Try a simple command execution as test
            try:
                # Simple echo command that should work if the agent is truly ready
                command_params = {'command': 'echo "ready"'}
                
                # Try the agent/exec API endpoint directly
                self._proxmoxer.nodes(node).qemu(vmid).agent.post('exec', **command_params)
                
                # If we get here without exception, the agent is ready for commands
                result["ready"] = True
                result["message"] = "VM agent is fully operational"
                
            except Exception as cmd_error:
                return {
                    'status': QemuStatus.failure,
                    'exception' : e
                }
            
        except Exception as e:
            return {
                'status': QemuStatus.failure,
                'exception' : e
            }
        
        return {"status" : QemuStatus.running}
    