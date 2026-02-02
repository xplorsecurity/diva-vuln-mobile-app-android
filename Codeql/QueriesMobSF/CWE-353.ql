/**
 * @name Missing authorization check
 * @description Detects public methods lacking authorization validation.
 * @kind problem
 * @problem.severity warning
 * @precision medium
 * @id java/cwe-353-missing-auth
 */

import java

from Method m
where
  m.isPublic() and
  not m.getBody().toString().matches("%(?i)(auth|authorize|permission|check)%")
select m, "Public method may lack authorization checks (CWE-353)."
