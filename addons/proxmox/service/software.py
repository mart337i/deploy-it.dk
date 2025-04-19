
import logging

from proxmox.enums.qemu import QemuStatus
from proxmox.service.qemu import QemuAgentManagement
from proxmoxer.core import ResourceException

from clicx.utils.jinja import render

_logger = logging.getLogger(__name__)

class SoftwareMangement(QemuAgentManagement):

#######################
# MARK: VM Configuration
#######################

    def install_docker_engine(self,node,vmid):
        script = render('install_docker.sh')
        return self.execute_shell_script(script, node, vmid)
    
    def pull_docker_image(self, node, vmid, image_name):
        shell_script = render("pull_image.sh", {
            "image_name":image_name
        })
        
        return self.execute_shell_script(shell_script, node, vmid)

    def start_docker_image(self, node, vmid, image_name, container_name, port_mapping="", volume_mapping="", env_vars=""):
        shell_script = render(
            template_name="start_docker_image.sh",
            context = {
                "image_name": image_name,
                "container_name": container_name,
                "port_mapping": port_mapping,
                "volume_mapping": volume_mapping,
                "env_vars": env_vars
            })


        return self.execute_shell_script(shell_script, node, vmid)

    def stop_docker_image(self, node, vmid, container_name, remove_container=False):
        shell_script = render(
            template_name="stop_docker_image.sh",
            context = {
            "container_name": container_name,
            "remove_container": remove_container
        })
        return self.execute_shell_script(shell_script, node, vmid)
    
    def create_proxy_conf(self, node, vmid, hostname, ip):
        shell_script = render(
            template_name="simple_create_proxy_conf.sh",
            context = {
            "hostname": hostname,
            "ip": ip
        })
        return self.execute_shell_script(shell_script, node, vmid)
    
    def create_proxy_for_docker_conf(self, node, vmid, hostname, ip, port, name):
        shell_script = render(
            template_name="create_proxy_conf.sh",
            context = {
            "hostname": hostname,
            "ip": ip,
            "port" : port,
            "name": name,
        })
        return self.execute_shell_script(shell_script, node, vmid)

    def configure_vm(self, node: str, vmid: str, script_name: str):
        """Execute a predefined shell script template on a VM"""
        # Check Qemu status
        qemu_available = self.await_qemu_agent_ready(node=node, vm_id=vmid)
        if qemu_available != QemuStatus.running:
            raise ResourceException(status_code=500, status_message="Qemu agent not running")
    
        try:
            # Render the script from template
            script_content = render(template_name=script_name)
            
            # Execute the shell script
            result = self.execute_shell_script(script_content=script_content, node=node, vmid=vmid)
            
            # Return job status
            return {
                "status": "completed" if result["status"] == "success" else "failed",
                "node": node,
                "vmid": vmid,
                "script_name": script_name,
                "result": result
            }
        
        except Exception as e:
            _logger.error(f"Failed to configure VM {vmid} on node {node}: {str(e)}")
            raise ResourceException(status_code=500, status_message=f"VM configuration failed: {str(e)}")
    
    def configure_vm_custom(self, node: str, vmid: str, script_file):
        """Execute a custom shell script uploaded by user on a VM"""
        # Check Qemu status
        qemu_available = self.await_qemu_agent_ready(node=node, vm_id=vmid)
        if qemu_available != QemuStatus.running:
            raise ResourceException(status_code=500, status_message="Qemu agent not running")
        
        try:
            # Read the content from the UploadFile object
            script_content = script_file.file.read().decode('utf-8')
            
            # Execute the shell script
            result = self.execute_shell_script(script_content=script_content, node=node, vmid=vmid)
            
            # Return job status
            return {
                "status": "completed" if result["status"] == "success" else "failed",
                "node": node,
                "vmid": vmid,
                "result": result
            }
        
        except Exception as e:
            _logger.error(f"Failed to configure VM {vmid} on node {node}: {str(e)}")
            raise ResourceException(status_code=500, status_message=f"VM configuration failed: {str(e)}")
    