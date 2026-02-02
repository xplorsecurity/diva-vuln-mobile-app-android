/**
 * @name Information exposure
 * @description Detects exposure of sensitive data in responses or logs.
 * @kind problem
 * @problem.severity warning
 * @precision medium
 * @id java/cwe-200-information-exposure
 */

import java

from StringLiteral s
where
  s.getValue().matches("%(?i)(internal error|stacktrace|exception)%")
select s, "Sensitive internal information may be exposed (CWE-200)."
