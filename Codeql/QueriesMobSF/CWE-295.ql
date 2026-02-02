/**
 * @name Insecure TLS certificate validation
 * @description Detects TrustManager implementations that accept all certificates.
 * @kind problem
 * @problem.severity error
 * @precision high
 * @id java/cwe-295-insecure-tls
 */

import java

from Class c, Method m
where
  c.getName().matches("%TrustManager%") and
  m.getName() = "checkServerTrusted" and
  m.getBody().toString() = "{}"
select m, "Certificate validation is disabled (CWE-295)."
