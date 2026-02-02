/**
 * @name Sensitive data logged
 * @description Detects logging of potentially sensitive information.
 * @kind problem
 * @problem.severity warning
 * @precision medium
 * @id java/cwe-532-sensitive-logging
 */

import java

from MethodAccess logCall, Expr arg
where
  logCall.getMethod().getDeclaringType().getName().matches("%Log%") and
  arg = logCall.getArgument(0) and
  arg.toString().matches("%(?i)(password|token|secret|apikey|authorization)%")
select logCall, "Sensitive information may be logged (CWE-532)."
