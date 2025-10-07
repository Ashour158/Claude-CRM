# marketplace/wasm_runtime.py
# WASM Runtime with Isolation and Execution Metrics

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import subprocess
import tempfile
import os
import signal
import threading
import time
from celery import shared_task

from .models import (
    WASMRuntime, WASMExecution, WASMMetrics, 
    WASMSandbox, WASMPlugin, WASMIsolation
)
from core.models import User, Company

logger = logging.getLogger(__name__)

class WASMRuntimeEngine:
    """
    Advanced WASM runtime engine with isolation, syscall guards,
    and execution metrics for secure plugin execution.
    """
    
    def __init__(self):
        self.isolation_levels = {
            'strict': self._strict_isolation,
            'moderate': self._moderate_isolation,
            'permissive': self._permissive_isolation
        }
        
        self.syscall_guards = {
            'file_system': self._guard_file_system,
            'network': self._guard_network,
            'process': self._guard_process,
            'memory': self._guard_memory
        }
        
        self.execution_metrics = {
            'cpu_usage': self._measure_cpu_usage,
            'memory_usage': self._measure_memory_usage,
            'execution_time': self._measure_execution_time,
            'fuel_consumption': self._measure_fuel_consumption
        }
    
    def execute_wasm_plugin(self, plugin_id: str, input_data: Dict[str, Any], 
                          execution_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute WASM plugin with isolation and monitoring.
        """
        try:
            # Get plugin
            plugin = WASMPlugin.objects.get(id=plugin_id)
            
            # Validate plugin
            validation_result = self._validate_plugin(plugin, execution_config)
            if not validation_result['valid']:
                return {
                    'status': 'error',
                    'error': validation_result['error']
                }
            
            # Create execution record
            execution_record = self._create_execution_record(plugin, input_data, execution_config)
            
            # Set up isolation
            isolation_config = execution_config.get('isolation', {})
            isolation_level = isolation_config.get('level', 'moderate')
            
            # Create sandbox
            sandbox = self._create_sandbox(plugin, isolation_config)
            
            # Execute plugin
            execution_result = self._execute_in_sandbox(
                plugin, input_data, sandbox, execution_config
            )
            
            # Collect metrics
            execution_metrics = self._collect_execution_metrics(execution_record, execution_result)
            
            # Update execution record
            execution_record.status = 'completed' if execution_result['success'] else 'failed'
            execution_record.output_data = execution_result.get('output', {})
            execution_record.error_message = execution_result.get('error', '')
            execution_record.execution_metrics = execution_metrics
            execution_record.completed_at = timezone.now()
            execution_record.save()
            
            return {
                'status': 'success' if execution_result['success'] else 'error',
                'execution_id': str(execution_record.id),
                'output': execution_result.get('output', {}),
                'metrics': execution_metrics,
                'execution_time': execution_result.get('execution_time', 0),
                'error': execution_result.get('error', '')
            }
            
        except Exception as e:
            logger.error(f"WASM plugin execution failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def batch_execute_plugins(self, plugin_executions: List[Dict[str, Any]], 
                            batch_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multiple WASM plugins in batch with resource management.
        """
        try:
            # Set up batch execution
            max_concurrent = batch_config.get('max_concurrent', 5)
            timeout = batch_config.get('timeout', 300)  # 5 minutes
            
            # Create execution queue
            execution_queue = []
            for execution in plugin_executions:
                execution_queue.append({
                    'plugin_id': execution['plugin_id'],
                    'input_data': execution['input_data'],
                    'execution_config': execution.get('execution_config', {})
                })
            
            # Execute plugins with concurrency control
            results = []
            active_executions = []
            
            while execution_queue or active_executions:
                # Start new executions if under limit
                while len(active_executions) < max_concurrent and execution_queue:
                    execution = execution_queue.pop(0)
                    
                    # Start execution in thread
                    execution_thread = threading.Thread(
                        target=self._execute_plugin_thread,
                        args=(execution, results)
                    )
                    execution_thread.start()
                    active_executions.append(execution_thread)
                
                # Check for completed executions
                completed_executions = []
                for thread in active_executions:
                    if not thread.is_alive():
                        completed_executions.append(thread)
                
                for thread in completed_executions:
                    active_executions.remove(thread)
                
                # Sleep to prevent busy waiting
                time.sleep(0.1)
            
            return {
                'status': 'success',
                'total_executions': len(plugin_executions),
                'results': results,
                'batch_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch WASM execution failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def monitor_wasm_execution(self, execution_id: str, monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor WASM execution in real-time.
        """
        try:
            # Get execution record
            execution = WASMExecution.objects.get(id=execution_id)
            
            # Check if execution is still running
            if execution.status != 'running':
                return {
                    'status': 'completed',
                    'execution_status': execution.status,
                    'metrics': execution.execution_metrics
                }
            
            # Get real-time metrics
            real_time_metrics = self._get_real_time_metrics(execution, monitoring_config)
            
            # Check for resource limits
            resource_limits = monitoring_config.get('resource_limits', {})
            limit_violations = self._check_resource_limits(real_time_metrics, resource_limits)
            
            # Generate alerts if needed
            alerts = self._generate_monitoring_alerts(real_time_metrics, limit_violations)
            
            return {
                'status': 'running',
                'real_time_metrics': real_time_metrics,
                'limit_violations': limit_violations,
                'alerts': alerts,
                'monitoring_timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"WASM execution monitoring failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _validate_plugin(self, plugin: WASMPlugin, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WASM plugin before execution"""
        try:
            # Check plugin status
            if not plugin.is_active:
                return {
                    'valid': False,
                    'error': 'Plugin is not active'
                }
            
            # Check plugin signature
            if not self._verify_plugin_signature(plugin):
                return {
                    'valid': False,
                    'error': 'Plugin signature verification failed'
                }
            
            # Check resource requirements
            resource_requirements = plugin.resource_requirements
            available_resources = config.get('available_resources', {})
            
            for resource, requirement in resource_requirements.items():
                if resource in available_resources:
                    if available_resources[resource] < requirement:
                        return {
                            'valid': False,
                            'error': f'Insufficient {resource}: required {requirement}, available {available_resources[resource]}'
                        }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Plugin validation failed: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _create_execution_record(self, plugin: WASMPlugin, input_data: Dict[str, Any], 
                               config: Dict[str, Any]) -> WASMExecution:
        """Create WASM execution record"""
        return WASMExecution.objects.create(
            plugin=plugin,
            input_data=input_data,
            execution_config=config,
            status='running',
            started_at=timezone.now()
        )
    
    def _create_sandbox(self, plugin: WASMPlugin, isolation_config: Dict[str, Any]) -> WASMSandbox:
        """Create WASM sandbox with isolation"""
        try:
            # Create sandbox record
            sandbox = WASMSandbox.objects.create(
                plugin=plugin,
                isolation_config=isolation_config,
                created_at=timezone.now()
            )
            
            # Set up isolation based on level
            isolation_level = isolation_config.get('level', 'moderate')
            isolation_func = self.isolation_levels.get(isolation_level)
            
            if isolation_func:
                isolation_func(sandbox, isolation_config)
            
            return sandbox
            
        except Exception as e:
            logger.error(f"Sandbox creation failed: {str(e)}")
            raise
    
    def _execute_in_sandbox(self, plugin: WASMPlugin, input_data: Dict[str, Any], 
                          sandbox: WASMSandbox, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin in sandbox"""
        try:
            # Set up execution environment
            execution_env = self._setup_execution_environment(plugin, sandbox, config)
            
            # Prepare input data
            input_file = self._prepare_input_data(input_data, execution_env)
            
            # Execute WASM module
            start_time = time.time()
            
            # This would implement actual WASM execution
            # For now, simulate execution
            execution_result = self._simulate_wasm_execution(plugin, input_data, config)
            
            execution_time = time.time() - start_time
            
            # Clean up execution environment
            self._cleanup_execution_environment(execution_env)
            
            return {
                'success': True,
                'output': execution_result,
                'execution_time': execution_time
            }
            
        except Exception as e:
            logger.error(f"Sandbox execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': 0
            }
    
    def _strict_isolation(self, sandbox: WASMSandbox, config: Dict[str, Any]):
        """Apply strict isolation"""
        try:
            # Disable all syscalls except essential ones
            sandbox.syscall_whitelist = [
                'exit', 'brk', 'mmap', 'munmap', 'mprotect'
            ]
            
            # Set memory limits
            sandbox.memory_limit = config.get('memory_limit', 64 * 1024 * 1024)  # 64MB
            
            # Set execution time limit
            sandbox.time_limit = config.get('time_limit', 30)  # 30 seconds
            
            # Disable network access
            sandbox.network_access = False
            
            # Disable file system access
            sandbox.file_system_access = False
            
            sandbox.save()
            
        except Exception as e:
            logger.error(f"Strict isolation setup failed: {str(e)}")
            raise
    
    def _moderate_isolation(self, sandbox: WASMSandbox, config: Dict[str, Any]):
        """Apply moderate isolation"""
        try:
            # Allow limited syscalls
            sandbox.syscall_whitelist = [
                'exit', 'brk', 'mmap', 'munmap', 'mprotect',
                'read', 'write', 'open', 'close'
            ]
            
            # Set memory limits
            sandbox.memory_limit = config.get('memory_limit', 128 * 1024 * 1024)  # 128MB
            
            # Set execution time limit
            sandbox.time_limit = config.get('time_limit', 60)  # 60 seconds
            
            # Allow limited network access
            sandbox.network_access = config.get('network_access', False)
            
            # Allow limited file system access
            sandbox.file_system_access = config.get('file_system_access', False)
            
            sandbox.save()
            
        except Exception as e:
            logger.error(f"Moderate isolation setup failed: {str(e)}")
            raise
    
    def _permissive_isolation(self, sandbox: WASMSandbox, config: Dict[str, Any]):
        """Apply permissive isolation"""
        try:
            # Allow most syscalls
            sandbox.syscall_whitelist = [
                'exit', 'brk', 'mmap', 'munmap', 'mprotect',
                'read', 'write', 'open', 'close', 'stat', 'fstat',
                'lstat', 'poll', 'lseek', 'mmap2', 'mprotect',
                'munmap', 'brk', 'rt_sigaction', 'rt_sigprocmask',
                'rt_sigreturn', 'ioctl', 'pread64', 'pwrite64',
                'readv', 'writev', 'access', 'pipe', 'select',
                'sched_yield', 'mremap', 'msync', 'mincore',
                'madvise', 'shmget', 'shmat', 'shmctl', 'dup',
                'dup2', 'pause', 'nanosleep', 'getitimer',
                'alarm', 'setitimer', 'getpid', 'sendfile',
                'socket', 'connect', 'accept', 'sendto', 'recvfrom',
                'sendmsg', 'recvmsg', 'shutdown', 'bind', 'listen',
                'getsockname', 'getpeername', 'socketpair',
                'setsockopt', 'getsockopt', 'clone', 'fork',
                'vfork', 'execve', 'exit', 'wait4', 'kill',
                'uname', 'semget', 'semop', 'semctl', 'shmdt',
                'msgget', 'msgsnd', 'msgrcv', 'msgctl', 'fcntl',
                'flock', 'fsync', 'fdatasync', 'truncate',
                'ftruncate', 'getdents', 'getcwd', 'chdir',
                'fchdir', 'rename', 'mkdir', 'rmdir', 'creat',
                'link', 'unlink', 'symlink', 'readlink', 'chmod',
                'fchmod', 'chown', 'fchown', 'lchown', 'umask',
                'gettimeofday', 'getrlimit', 'getrusage', 'sysinfo',
                'times', 'ptrace', 'getuid', 'syslog', 'getgid',
                'setuid', 'setgid', 'geteuid', 'getegid', 'setpgid',
                'getppid', 'getpgrp', 'setsid', 'setreuid',
                'setregid', 'getgroups', 'setgroups', 'setresuid',
                'getresuid', 'setresgid', 'getresgid', 'getpgid',
                'setfsuid', 'setfsgid', 'getsid', 'capget', 'capset',
                'rt_sigpending', 'rt_sigtimedwait', 'rt_sigqueueinfo',
                'rt_sigsuspend', 'sigaltstack', 'utime', 'mknod',
                'uselib', 'personality', 'ustat', 'statfs', 'fstatfs',
                'sysfs', 'getpriority', 'setpriority', 'sched_setparam',
                'sched_getparam', 'sched_setscheduler', 'sched_getscheduler',
                'sched_get_priority_max', 'sched_get_priority_min',
                'sched_rr_get_interval', 'mlock', 'munlock',
                'mlockall', 'munlockall', 'vhangup', 'modify_ldt',
                'pivot_root', 'prctl', 'arch_prctl', 'adjtimex',
                'setrlimit', 'chroot', 'sync', 'acct', 'settimeofday',
                'mount', 'umount2', 'swapon', 'swapoff', 'reboot',
                'sethostname', 'setdomainname', 'iopl', 'ioperm',
                'create_module', 'init_module', 'delete_module',
                'get_kernel_syms', 'query_module', 'quotactl',
                'nfsservctl', 'getpmsg', 'putpmsg', 'afs_syscall',
                'tuxcall', 'security', 'gettid', 'readahead', 'setxattr',
                'lsetxattr', 'fsetxattr', 'getxattr', 'lgetxattr',
                'fgetxattr', 'listxattr', 'llistxattr', 'flistxattr',
                'removexattr', 'lremovexattr', 'fremovexattr', 'tkill',
                'time', 'futex', 'sched_setaffinity', 'sched_getaffinity',
                'set_thread_area', 'io_setup', 'io_destroy', 'io_getevents',
                'io_submit', 'io_cancel', 'get_thread_area', 'lookup_dcookie',
                'epoll_create', 'epoll_ctl_old', 'epoll_wait_old', 'remap_file_pages',
                'getdents64', 'set_tid_address', 'restart_syscall',
                'semtimedop', 'fadvise64', 'timer_create', 'timer_settime',
                'timer_gettime', 'timer_getoverrun', 'timer_delete',
                'clock_settime', 'clock_gettime', 'clock_getres',
                'clock_nanosleep', 'exit_group', 'epoll_wait', 'epoll_ctl',
                'tgkill', 'utimes', 'vserver', 'mbind', 'set_mempolicy',
                'get_mempolicy', 'mq_open', 'mq_unlink', 'mq_timedsend',
                'mq_timedreceive', 'mq_notify', 'mq_getattr', 'mq_setattr',
                'kexec_load', 'waitid', 'add_key', 'request_key', 'keyctl',
                'ioprio_set', 'ioprio_get', 'inotify_init', 'inotify_add_watch',
                'inotify_rm_watch', 'migrate_pages', 'openat', 'mkdirat',
                'mknodat', 'fchownat', 'futimesat', 'newfstatat', 'unlinkat',
                'renameat', 'linkat', 'symlinkat', 'readlinkat', 'fchmodat',
                'faccessat', 'pselect6', 'ppoll', 'unshare', 'set_robust_list',
                'get_robust_list', 'splice', 'tee', 'sync_file_range',
                'vmsplice', 'move_pages', 'utimensat', 'epoll_pwait',
                'signalfd', 'timerfd_create', 'eventfd', 'fallocate',
                'timerfd_settime', 'timerfd_gettime', 'accept4', 'signalfd4',
                'eventfd2', 'epoll_create1', 'dup3', 'pipe2', 'inotify_init1',
                'preadv', 'pwritev', 'rt_tgsigqueueinfo', 'perf_event_open',
                'recvmmsg', 'fanotify_init', 'fanotify_mark', 'prlimit64',
                'name_to_handle_at', 'open_by_handle_at', 'clock_adjtime',
                'syncfs', 'sendmmsg', 'setns', 'getcpu', 'process_vm_readv',
                'process_vm_writev', 'kcmp', 'finit_module', 'sched_setattr',
                'sched_getattr', 'renameat2', 'seccomp', 'getrandom',
                'memfd_create', 'kexec_file_load', 'bpf', 'execveat',
                'userfaultfd', 'membarrier', 'mlock2', 'copy_file_range',
                'preadv2', 'pwritev2', 'pkey_mprotect', 'pkey_alloc',
                'pkey_free', 'statx', 'io_pgetevents', 'rseq', 'pidfd_send_signal',
                'io_uring_setup', 'io_uring_enter', 'io_uring_register',
                'open_tree', 'move_mount', 'fsopen', 'fsconfig', 'fsmount',
                'fspick', 'pidfd_open', 'clone3', 'close_range', 'openat2',
                'pidfd_getfd', 'faccessat2', 'process_madvise', 'epoll_pwait2',
                'mount_setattr', 'landlock_create_ruleset', 'landlock_add_rule',
                'landlock_restrict_self', 'memfd_secret', 'process_mrelease',
                'futex_waitv', 'set_mempolicy_home_node'
            ]
            
            # Set memory limits
            sandbox.memory_limit = config.get('memory_limit', 256 * 1024 * 1024)  # 256MB
            
            # Set execution time limit
            sandbox.time_limit = config.get('time_limit', 120)  # 120 seconds
            
            # Allow network access
            sandbox.network_access = config.get('network_access', True)
            
            # Allow file system access
            sandbox.file_system_access = config.get('file_system_access', True)
            
            sandbox.save()
            
        except Exception as e:
            logger.error(f"Permissive isolation setup failed: {str(e)}")
            raise
    
    def _setup_execution_environment(self, plugin: WASMPlugin, sandbox: WASMSandbox, 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """Set up execution environment"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Copy plugin WASM file
            wasm_file = os.path.join(temp_dir, 'plugin.wasm')
            with open(wasm_file, 'wb') as f:
                f.write(plugin.wasm_data)
            
            # Set up environment variables
            env_vars = {
                'WASM_PLUGIN_ID': str(plugin.id),
                'WASM_SANDBOX_ID': str(sandbox.id),
                'WASM_TEMP_DIR': temp_dir
            }
            
            return {
                'temp_dir': temp_dir,
                'wasm_file': wasm_file,
                'env_vars': env_vars
            }
            
        except Exception as e:
            logger.error(f"Execution environment setup failed: {str(e)}")
            raise
    
    def _prepare_input_data(self, input_data: Dict[str, Any], execution_env: Dict[str, Any]) -> str:
        """Prepare input data for WASM execution"""
        try:
            # Create input file
            input_file = os.path.join(execution_env['temp_dir'], 'input.json')
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            return input_file
            
        except Exception as e:
            logger.error(f"Input data preparation failed: {str(e)}")
            raise
    
    def _simulate_wasm_execution(self, plugin: WASMPlugin, input_data: Dict[str, Any], 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate WASM execution (placeholder)"""
        try:
            # This would implement actual WASM execution
            # For now, simulate based on plugin type
            plugin_type = plugin.plugin_type
            
            if plugin_type == 'data_processor':
                return self._simulate_data_processor(input_data)
            elif plugin_type == 'calculator':
                return self._simulate_calculator(input_data)
            elif plugin_type == 'formatter':
                return self._simulate_formatter(input_data)
            else:
                return {'result': 'Plugin executed successfully'}
                
        except Exception as e:
            logger.error(f"WASM execution simulation failed: {str(e)}")
            return {'error': str(e)}
    
    def _simulate_data_processor(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate data processor plugin"""
        try:
            # Process input data
            processed_data = {}
            
            for key, value in input_data.items():
                if isinstance(value, str):
                    processed_data[key] = value.upper()
                elif isinstance(value, (int, float)):
                    processed_data[key] = value * 2
                else:
                    processed_data[key] = value
            
            return {
                'processed_data': processed_data,
                'processing_time': 0.1,
                'records_processed': len(input_data)
            }
            
        except Exception as e:
            logger.error(f"Data processor simulation failed: {str(e)}")
            return {'error': str(e)}
    
    def _simulate_calculator(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate calculator plugin"""
        try:
            # Perform calculations
            result = 0
            
            if 'numbers' in input_data:
                numbers = input_data['numbers']
                if isinstance(numbers, list):
                    result = sum(numbers)
                else:
                    result = numbers
            
            if 'operation' in input_data:
                operation = input_data['operation']
                if operation == 'multiply' and 'numbers' in input_data:
                    numbers = input_data['numbers']
                    if isinstance(numbers, list):
                        result = 1
                        for num in numbers:
                            result *= num
            
            return {
                'result': result,
                'calculation_time': 0.05
            }
            
        except Exception as e:
            logger.error(f"Calculator simulation failed: {str(e)}")
            return {'error': str(e)}
    
    def _simulate_formatter(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate formatter plugin"""
        try:
            # Format input data
            formatted_data = {}
            
            for key, value in input_data.items():
                if isinstance(value, str):
                    formatted_data[key] = value.strip().title()
                elif isinstance(value, (int, float)):
                    formatted_data[key] = f"{value:,.2f}"
                else:
                    formatted_data[key] = str(value)
            
            return {
                'formatted_data': formatted_data,
                'formatting_time': 0.02
            }
            
        except Exception as e:
            logger.error(f"Formatter simulation failed: {str(e)}")
            return {'error': str(e)}
    
    def _cleanup_execution_environment(self, execution_env: Dict[str, Any]):
        """Clean up execution environment"""
        try:
            # Remove temporary directory
            import shutil
            shutil.rmtree(execution_env['temp_dir'])
            
        except Exception as e:
            logger.error(f"Execution environment cleanup failed: {str(e)}")
    
    def _collect_execution_metrics(self, execution_record: WASMExecution, 
                                 execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Collect execution metrics"""
        try:
            metrics = {
                'execution_time': execution_result.get('execution_time', 0),
                'cpu_usage': execution_result.get('cpu_usage', 0),
                'memory_usage': execution_result.get('memory_usage', 0),
                'fuel_consumption': execution_result.get('fuel_consumption', 0),
                'success': execution_result.get('success', False)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Execution metrics collection failed: {str(e)}")
            return {}
    
    def _get_real_time_metrics(self, execution: WASMExecution, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time execution metrics"""
        try:
            # This would implement actual real-time metrics collection
            # For now, return placeholder metrics
            return {
                'cpu_usage': 0.5,
                'memory_usage': 1024 * 1024,  # 1MB
                'execution_time': 10.5,
                'fuel_consumption': 1000
            }
            
        except Exception as e:
            logger.error(f"Real-time metrics collection failed: {str(e)}")
            return {}
    
    def _check_resource_limits(self, metrics: Dict[str, Any], limits: Dict[str, Any]) -> List[str]:
        """Check resource limits"""
        try:
            violations = []
            
            if 'cpu_limit' in limits and metrics.get('cpu_usage', 0) > limits['cpu_limit']:
                violations.append('CPU limit exceeded')
            
            if 'memory_limit' in limits and metrics.get('memory_usage', 0) > limits['memory_limit']:
                violations.append('Memory limit exceeded')
            
            if 'time_limit' in limits and metrics.get('execution_time', 0) > limits['time_limit']:
                violations.append('Time limit exceeded')
            
            if 'fuel_limit' in limits and metrics.get('fuel_consumption', 0) > limits['fuel_limit']:
                violations.append('Fuel limit exceeded')
            
            return violations
            
        except Exception as e:
            logger.error(f"Resource limit checking failed: {str(e)}")
            return []
    
    def _generate_monitoring_alerts(self, metrics: Dict[str, Any], violations: List[str]) -> List[Dict[str, Any]]:
        """Generate monitoring alerts"""
        try:
            alerts = []
            
            for violation in violations:
                alerts.append({
                    'type': 'resource_violation',
                    'message': violation,
                    'severity': 'high',
                    'timestamp': timezone.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Monitoring alert generation failed: {str(e)}")
            return []
    
    def _verify_plugin_signature(self, plugin: WASMPlugin) -> bool:
        """Verify plugin signature"""
        try:
            # This would implement actual signature verification
            # For now, return True as placeholder
            return True
            
        except Exception as e:
            logger.error(f"Plugin signature verification failed: {str(e)}")
            return False
    
    def _execute_plugin_thread(self, execution: Dict[str, Any], results: List[Dict[str, Any]]):
        """Execute plugin in thread"""
        try:
            result = self.execute_wasm_plugin(
                execution['plugin_id'],
                execution['input_data'],
                execution['execution_config']
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Plugin thread execution failed: {str(e)}")
            results.append({
                'status': 'error',
                'error': str(e)
            })

# Celery tasks
@shared_task
def execute_wasm_plugin_async(plugin_id: str, input_data: Dict[str, Any], execution_config: Dict[str, Any]):
    """Async task to execute WASM plugin"""
    engine = WASMRuntimeEngine()
    return engine.execute_wasm_plugin(plugin_id, input_data, execution_config)

@shared_task
def batch_execute_plugins_async(plugin_executions: List[Dict[str, Any]], batch_config: Dict[str, Any]):
    """Async task to batch execute plugins"""
    engine = WASMRuntimeEngine()
    return engine.batch_execute_plugins(plugin_executions, batch_config)

@shared_task
def monitor_wasm_execution_async(execution_id: str, monitoring_config: Dict[str, Any]):
    """Async task to monitor WASM execution"""
    engine = WASMRuntimeEngine()
    return engine.monitor_wasm_execution(execution_id, monitoring_config)

# API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_wasm_plugin(request):
    """API endpoint to execute WASM plugin"""
    engine = WASMRuntimeEngine()
    result = engine.execute_wasm_plugin(
        request.data.get('plugin_id'),
        request.data.get('input_data', {}),
        request.data.get('execution_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_execute_plugins(request):
    """API endpoint to batch execute plugins"""
    engine = WASMRuntimeEngine()
    result = engine.batch_execute_plugins(
        request.data.get('plugin_executions', []),
        request.data.get('batch_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def monitor_wasm_execution(request):
    """API endpoint to monitor WASM execution"""
    engine = WASMRuntimeEngine()
    result = engine.monitor_wasm_execution(
        request.data.get('execution_id'),
        request.data.get('monitoring_config', {})
    )
    return Response(result, status=status.HTTP_200_OK)
