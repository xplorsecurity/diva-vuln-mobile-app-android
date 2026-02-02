/**
 * @name Weak Cryptographic Algorithm
 * @description Detects usage of weak cryptographic hash algorithms.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id java/mobsf-weak-crypto
 */

import java

from MethodAccess m
where
  m.getMethod().getName() = "getInstance" and
  m.getArgument(0).(StringLiteral).getValue().matches("%(?i)(md5|sha1)%")
select m, "Weak cryptographic algorithm detected."
