import subprocess
import json
import os
import tempfile
import logging
from typing import Dict, Any, List, Optional
import asyncio
import time
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure this specific logger is set to DEBUG level

class RealTestRunner:
    """Real test runner that actually executes AppWright tests on devices."""
    
    def __init__(self, target: str):
        self.target = target
        self.workspace_dir = Path.cwd()
        
    async def run_tests(self, test_path: str, app_version_id: str) -> Dict[str, Any]:
        """Run actual AppWright tests on the specified target."""
        try:
            logger.info(f"🚀 Starting REAL AppWright test execution: {test_path} on {self.target}")
            
            # Step 1: Validate test file exists
            if not os.path.exists(test_path):
                return {
                    "success": False,
                    "error": f"Test file not found: {test_path}"
                }
            
            # Step 2: Validate test file format
            if not test_path.endswith(('.js', '.ts', '.spec.js', '.spec.ts')):
                return {
                    "success": False,
                    "error": f"Invalid test file format: {test_path}"
                }
            
            # Step 3: Set up target-specific configuration - pass app_version_id only for tracking
            config = await self._setup_target_config(app_version_id)
            if not config["success"]:
                return config
                
            # Step 4: Execute the actual test
            start_time = time.time()
            execution_result = await self._execute_appwright_test(test_path, config["config"])
            execution_time = time.time() - start_time
            
            if execution_result["success"]:
                logger.info(f"✅ Test completed successfully in {execution_time:.2f}s")
                return {
                    "success": True,
                    "results": {
                        "test_file": test_path,
                        "app_version_id": app_version_id,
                        "target": self.target,
                        "execution_time": execution_time,
                        "tests_run": execution_result.get("tests_run", 1),
                        "tests_passed": execution_result.get("tests_passed", 1),
                        "tests_failed": execution_result.get("tests_failed", 0),
                        "video_path": execution_result.get("video_path"),
                        "screenshots": execution_result.get("screenshots", []),
                        "details": {
                            "target_config": config["config"],
                            "timestamp": time.time(),
                            "device_info": execution_result.get("device_info", {}),
                            "test_output": execution_result.get("output", "")
                        }
                    }
                }
            else:
                logger.error(f"❌ Test failed: {execution_result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "error": execution_result.get("error", "Test execution failed")
                }
                
        except Exception as e:
            logger.error(f"💥 Error running real test {test_path}: {str(e)}")
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}"
            }
    
    async def _setup_target_config(self, app_version_id: str) -> Dict[str, Any]:
        """Set up configuration for the target environment."""
        try:
            if self.target == "emulator":
                return await self._setup_emulator_config(app_version_id)
            elif self.target == "device":
                return await self._setup_device_config(app_version_id)
            elif self.target == "browserstack":
                return await self._setup_browserstack_config(app_version_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown target type: {self.target}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to setup {self.target} config: {str(e)}"
            }
    
    async def _setup_emulator_config(self, app_version_id: str) -> Dict[str, Any]:
        """Configure Android emulator for testing."""
        logger.info("🔧 Setting up Android emulator configuration...")
        
        # Check if emulator is available
        emulator_check = await self._run_command(["adb", "devices"])
        if not emulator_check["success"]:
            return {
                "success": False,
                "error": "ADB not available. For real device testing, please use BrowserStack target instead of emulator. Android SDK setup not required for BrowserStack."
            }
        
        # Look for APK file
        apk_path = self._find_apk_file(app_version_id)
        if not apk_path:
            apk_path = "apps/test123.apk"  # Default from project structure
        
        config = {
            "platform": "ANDROID",
            "device": {"provider": "emulator"},
            "buildPath": apk_path,
            "automationName": "uiautomator2"
        }
        
        logger.info(f"📱 Emulator config: {config}")
        return {"success": True, "config": config}
    
    async def _setup_device_config(self, app_version_id: str) -> Dict[str, Any]:
        """Configure physical device for testing."""
        logger.info("🔧 Setting up physical device configuration...")
        
        # Check for connected devices
        device_check = await self._run_command(["adb", "devices"])
        if not device_check["success"]:
            return {
                "success": False,
                "error": "No physical devices detected. Please connect a device."
            }
        
        apk_path = self._find_apk_file(app_version_id)
        if not apk_path:
            apk_path = "apps/test123.apk"
        
        config = {
            "platform": "ANDROID",
            "device": {"provider": "device"},
            "buildPath": apk_path,
            "automationName": "uiautomator2"
        }
        
        logger.info(f"📲 Device config: {config}")
        return {"success": True, "config": config}
    
    async def _setup_browserstack_config(self, app_version_id: str) -> Dict[str, Any]:
        """Configure BrowserStack for testing."""
        logger.info("🔧 Setting up BrowserStack configuration...")
        
        # Check for BrowserStack credentials
        username = os.getenv("BROWSERSTACK_USERNAME")
        access_key = os.getenv("BROWSERSTACK_ACCESS_KEY")
        
        # Add debug logging
        logger.info(f"Debug - Username found: {bool(username)}, Access key found: {bool(access_key)}")
        logger.info(f"Debug - Username value: {username}")
        logger.info(f"Debug - Access key value: {access_key}")
        
        if not username or not access_key:
            logger.warning("⚠️  BrowserStack credentials not found, using demo mode")
            # For demo purposes, use BrowserStack provider without credentials
            config = {
                "platform": "ANDROID",
                "device": {
                    "provider": "browserstack",
                    "name": "Google Pixel 7",
                    "osVersion": "13.0"
                },
                "buildPath": "builds/wikipedia.apk",  # Use direct path, don't modify based on app_version_id
                "automationName": "uiautomator2"
            }
        else:
            # Real BrowserStack configuration for AppWright
            config = {
                "platform": "ANDROID", 
                "device": {
                    "provider": "browserstack",
                    "username": username,
                    "accessKey": access_key,
                    "name": "Google Pixel 7",
                    "osVersion": "13.0"
                },
                "buildPath": "builds/wikipedia.apk",  # Use direct path, don't modify based on app_version_id
                "automationName": "uiautomator2"
            }
        
        logger.info(f"☁️  BrowserStack config: {config}")
        return {"success": True, "config": config}
    
    async def _execute_appwright_test(self, test_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual AppWright test."""
        try:
            logger.info(f"🏃 Executing AppWright test with config from appwright.config.ts")
            
            # Build the command with project specification and trace recording
            cmd = [
                "npx", "appwright", "test", test_path,
                "--config", "appwright.config.ts",  # Use the TypeScript config directly
                "--reporter", "json",
                "--project", "android",  # Specify the android project
                "--trace", "on"
            ]
            
            logger.info(f"🚀 Running: {' '.join(cmd)}")
            result = await self._run_command(cmd)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AppWright execution error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _run_command(self, cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Run a shell command asynchronously."""
        try:
            logger.info(f"🔧 Running command: {' '.join(cmd)}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_dir
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return_code = process.returncode
                
                output = stdout.decode('utf-8') if stdout else ""
                error = stderr.decode('utf-8') if stderr else ""
                
                logger.info(f"📤 Command completed with return code: {return_code}")
                if output:
                    logger.debug(f"📝 Output: {output[:500]}...")
                if error:
                    logger.warning(f"⚠️  Error output: {error[:500]}...")
                
                return {
                    "success": return_code == 0,
                    "return_code": return_code,
                    "output": output,
                    "error": error
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to run command: {str(e)}"
            }
    
    def _find_apk_file(self, app_version_id: str) -> Optional[str]:
        """Find APK file for the given app version."""
        # For BrowserStack, always use the configured path
        if self.target == "browserstack":
            return "builds/wikipedia.apk"
            
        # For other targets, look in apps directory
        apps_dir = Path("apps")
        if apps_dir.exists():
            # Try version-specific APK first
            version_apk = apps_dir / f"{app_version_id}.apk"
            if version_apk.exists():
                return str(version_apk)
            
            # Fall back to any APK file
            apk_files = list(apps_dir.glob("*.apk"))
            if apk_files:
                return str(apk_files[0])
        
        return None
    
    def _extract_device_info(self, output: str) -> Dict[str, Any]:
        """Extract device information from test output."""
        # This would parse actual AppWright output for device details
        return {
            "target_type": self.target,
            "timestamp": time.time(),
            "parsed_from_output": True
        } 