/**
 * @name OS Command Injection
 * @description Detects execution of system commands built from user input.
 * @kind problem
 * @problem.severity error
 * @precision high
 * @id java/cwe-78-command-injection
 */

import java

from MethodAccess m
where
  m.getMethod().getName() in ["exec", "start"] and
  m.getQualifier().getType().getName().matches("%Runtime%|ProcessBuilder%")
select m, "Possible OS command injection (CWE-78)."

