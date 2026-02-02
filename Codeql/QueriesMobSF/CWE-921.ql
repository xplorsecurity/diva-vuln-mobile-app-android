/**
 * @name Improper restriction of communication channel
 * @description Detects use of insecure protocols such as HTTP.
 * @kind problem
 * @problem.severity warning
 * @precision medium
 * @id java/cwe-921-improper-channel
 */

import java

from StringLiteral s
where
  s.getValue().matches("http://%")
select s, "Insecure communication channel detected (CWE-921)."
