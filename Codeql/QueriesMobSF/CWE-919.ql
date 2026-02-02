/**
 * @name Weak password policy
 * @description Detects weak password length checks.
 * @kind problem
 * @problem.severity warning
 * @precision low
 * @id java/cwe-919-weak-password-policy
 */

import java

from MethodAccess m
where
  m.getMethod().getName().matches("%length%") and
  m.toString().matches("%< 6%")
select m, "Weak password policy detected (CWE-919)."
