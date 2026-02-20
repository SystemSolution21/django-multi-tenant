# Platform-Initiated Tenant Creation

This document explains why platform-initiated tenant creation is practical and often required in real-world SaaS, and it summarizes secure, usable patterns for provisioning tenants and delivering initial access (temporary credentials and notifications).

## Why platform-initiated tenant creation is practical

- **Managed onboarding for enterprise clients:**
  - *White-glove service*: Large clients frequently expect the provider to provision and configure the tenant (sales engineers, account managers, or support staff). They expect a ready-to-use environment rather than self-service signup.
  - *Complex setup*: Products that require integrations, data migration, or custom configuration are easier and safer to provision from the platform side prior to handoff.
  - *Contractual triggers*: Provisioning may depend on signed contracts or billing activation, so the platform must create the tenant before access is granted.

- **Internal testing and demonstrations:**
  - *Sales demos*: Sales teams create tenant instances for tailored demonstrations and temporary demo users.
  - *QA / staging*: Internal teams spin up tenants to test features or reproduce customer issues without touching production tenant data.

- **Reseller / partner models:**
  - Partners or resellers may provision tenants on behalf of their customers. The platform must provide admin provisioning tools and APIs for partner-initiated tenant creation.

## Temporary passwords and notification patterns

- **Initial access**: Provide a temporary credential or a secure “set your password” link so the tenant owner can access the newly provisioned environment.

- **Forced password reset**: Require the user to set a new password on first login. This ensures the temporary credential cannot be reused or intercepted.

- **Email notification**: Send a clear email to the tenant owner containing the login URL and instructions. For better security, prefer a one-time link to set a password over communicating a plaintext temporary password when possible.

## Security considerations for temporary credentials

- **Generation**: Generate strong, random temporary passwords or tokens.

- **Transmission**: Email is common but not fully secure. Consider alternatives for high-sensitivity tenants:
  - Send a one-time link (tokenized, single-use) to set a password instead of the password itself.
  - Use SMS or out-of-band channels only if those channels meet your security policy.

- **Expiration**: Expire temporary credentials quickly (typical window: 24–48 hours).

- **Storage**: Never store temporary passwords in plaintext. If storing tokens, store hashed values and treat them as single-use secrets.

## Usability best practices

- **Clear instructions**: Email should clearly state where to log in, the temporary credential behavior, and that a password reset is mandatory.

- **Seamless first login**: Guide the user immediately into the password-reset flow after they authenticate with a temporary credential. Reduce friction in this step to increase successful onboarding.

- **Support path**: Include contact details and troubleshooting guidance in the notification in case the recipient does not receive or cannot use the temporary credential.

## Audit and compliance

- **Provisioning audit trail**: Log who (global superuser, sales engineer, partner account) provisioned the tenant, when, and for which account. Include relevant context such as contract ID or request ID.

- **Monitoring and retention**: Keep records according to your compliance needs and ensure logs are tamper-evident and accessible for audits.

## Operational recommendations (summary)

- **When to use platform-initiated creation**: enterprise white-glove onboarding, complex integrations, contract-triggered provisioning, internal demo/QA needs, and partner/reseller workflows.

- **How to implement temporary access safely**: use strong random tokens, prefer one-time password-set links, expire tokens quickly, avoid plaintext storage, and require mandatory first-login resets.

- **User experience**: send clear instructions, direct users to a guided password reset on first login, and include support contacts.

- **Auditability**: record who provisioned the tenant and keep secure logs for compliance and troubleshooting.

## Conclusion

Platform-initiated tenant creation is a common, practical requirement for many SaaS models. When implemented with secure temporary-access patterns, clear user guidance, and robust auditing, it supports enterprise onboarding, internal workflows, and reseller scenarios while protecting customer security and delivering a smooth first-time experience.
