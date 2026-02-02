/**
 * @name Hardcoded Secret
 * @description Detects hardcoded secrets such as API keys, tokens, and passwords.
 * @kind problem
 * @problem.severity error
 * @precision high
 * @id java/mobsf-hardcoded-secret
 */

import java

from StringLiteral s
where
  s.getValue().length() > 20 and
  s.getValue().matches("%(?i)(api|key|token|secret|password)%")
select s, "Possible hardcoded secret detected."
