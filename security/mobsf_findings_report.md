# MobSF Security Findings

## Hidden elements in view can be used to hide data from user. But this data can be leaked. If the view contains sensitive data, it might still be accessible through memory inspection. A good practice is to clear sensitive data before hiding it.
- File: app/src/main/java/jakhar/aseem/diva/AccessControl3NotesActivity.java:72

## Hidden elements in view can be used to hide data from user. But this data can be leaked. If the view contains sensitive data, it might still be accessible through memory inspection. A good practice is to clear sensitive data before hiding it.
- File: app/src/main/java/jakhar/aseem/diva/AccessControl3NotesActivity.java:73

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/InsecureDataStorage2Activity.java:57

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/InsecureDataStorage2Activity.java:71

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/InsecureDataStorage3Activity.java:72

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/InsecureDataStorage4Activity.java:71

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/LogActivity.java:50

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/LogActivity.java:56

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/SQLInjectionActivity.java:61

## The App logs information. Please ensure that sensitive information is never logged.
- File: app/src/main/java/jakhar/aseem/diva/SQLInjectionActivity.java:85

## App uses SQLite Database and execute raw SQL query. Untrusted user input in raw SQL queries can cause SQL Injection. Also sensitive information should be encrypted and written to the database.
- File: app/src/main/java/jakhar/aseem/diva/InsecureDataStorage2Activity.java:67

## App uses SQLite Database and execute raw SQL query. Untrusted user input in raw SQL queries can cause SQL Injection. Also sensitive information should be encrypted and written to the database.
- File: app/src/main/java/jakhar/aseem/diva/SQLInjectionActivity.java:70

## This flag allows anyone to backup your application data via adb. It allows users who have enabled USB debugging to copy application data off of the device.
- File: file:///home/runner/work/diva-vuln-mobile-app-android/diva-vuln-mobile-app-android/app/src/main/AndroidManifest.xml:1

## This app does not have root detection capabilities. Running a sensitive application on a rooted device questions the device integrity and affects users data.
- File: .:1

## This app does not use a TLS/SSL certificate or public key pinning in code to detect or prevent MITM attacks in secure communication channel. Please verify if pinning is enabled in `network_security_config.xml`.
- File: .:1

## This app does not uses SafetyNet Attestation API that provides cryptographically-signed attestation, assessing the device's integrity. This check helps to ensure that the servers are interacting with the genuine app running on a genuine Android device. 
- File: .:1

## This app does not have capabilities to prevent tapjacking attacks. An attacker can hijack the user's taps and tricks him into performing some critical operations that he did not intend to.
- File: .:1

## This app does not have capabilities to prevent against Screenshots from Recent Task History/ Now On Tap etc.
- File: .:1

## This app does not enforce TLS Certificate Transparency that helps to detect SSL certificates that have been mistakenly issued by a certificate authority or maliciously acquired from an otherwise unimpeachable certificate authority.
- File: .:1

