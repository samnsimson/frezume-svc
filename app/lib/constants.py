# Error Messages - Authentication & Authorization
ERROR_USER_NOT_FOUND = "User not found"
ERROR_USER_HAS_NO_ACCOUNT = "User has no account"
ERROR_EMAIL_NOT_VERIFIED = "Email not verified"
ERROR_INVALID_CREDENTIALS = "Invalid credentials"
ERROR_USERNAME_OR_EMAIL_EXISTS = "Username or email already exists"
ERROR_UNAUTHORIZED = "Unauthorized"
ERROR_INVALID_TOKEN = "Invalid token"
ERROR_TOKEN_EXPIRED = "Token expired"
ERROR_INVALID_OR_EXPIRED_TOKEN = "Invalid or expired token"
ERROR_USER_OR_SESSION_NOT_FOUND = "User or session not found"
ERROR_INVALID_SESSION_TOKEN = "Invalid session token"
ERROR_FAILED_TO_SIGN_OUT = "Failed to sign out"
ERROR_TOKEN_DOES_NOT_BELONG_TO_USER = "Token does not belong to the user"
ERROR_INVALID_IDENTIFIER = "Invalid identifier"
ERROR_FAILED_TO_VERIFY_EMAIL = "Failed to verify email"

# Error Messages - Database
ERROR_DATABASE_CONSTRAINT_VIOLATION = "A database constraint violation occurred"
ERROR_USERNAME_ALREADY_EXISTS = "Username already exists"
ERROR_EMAIL_ALREADY_EXISTS = "Email already exists"
ERROR_RECORD_ALREADY_EXISTS = "A record with this information already exists"
ERROR_REFERENCED_RECORD_NOT_EXISTS = "Referenced record does not exist"
ERROR_REQUIRED_FIELD_MISSING = "Required field is missing"
ERROR_DATABASE_ERROR = "A database error occurred"
ERROR_UNKNOWN_ERROR = "UnknownError"

# Error Messages - External Services
ERROR_RESOURCE_NOT_FOUND = "The requested resource was not found"
ERROR_ACCESS_DENIED = "Access denied to the requested resource"
ERROR_SERVICE_UNAVAILABLE = "External service is temporarily unavailable"
ERROR_FAILED_TO_SEND_EMAIL = "Failed to send email: {error}"
ERROR_FAILED_TO_CREATE_STRIPE_CUSTOMER = "Failed to create Stripe customer: {error}"
ERROR_FAILED_TO_CREATE_CHECKOUT_SESSION = "Failed to create checkout session: {error}"
ERROR_FAILED_TO_CREATE_PORTAL_SESSION = "Failed to create portal session: {error}"
ERROR_FAILED_TO_CANCEL_SUBSCRIPTION = "Failed to cancel subscription: {error}"
ERROR_FAILED_TO_UPDATE_SUBSCRIPTION = "Failed to update subscription: {error}"
ERROR_FAILED_TO_LINK_STRIPE_SUBSCRIPTION = "Failed to link Stripe subscription: {error}"
ERROR_FAILED_TO_SYNC_SUBSCRIPTION = "Failed to sync subscription: {error}"
ERROR_FAILED_TO_CREATE_STRIPE_SUBSCRIPTION = "Failed to create Stripe subscription: {error}"
ERROR_FAILED_TO_CANCEL_STRIPE_SUBSCRIPTION = "Failed to cancel Stripe subscription: {error}"
ERROR_FAILED_TO_UPDATE_STRIPE_SUBSCRIPTION = "Failed to update Stripe subscription: {error}"
ERROR_FAILED_TO_RETRIEVE_STRIPE_SUBSCRIPTION = "Failed to retrieve Stripe subscription: {error}"
ERROR_SUBSCRIPTION_NOT_FOUND = "Subscription not found"
ERROR_SUBSCRIPTION_NO_STRIPE_CUSTOMER = "Subscription has no Stripe customer"
ERROR_INVALID_PAYLOAD = "Invalid payload"
ERROR_INVALID_SIGNATURE = "Invalid signature"

# Error Messages - Validation & AI
ERROR_VALIDATION_ERROR = "Validation error"
ERROR_MODEL_RESPONSE_TRUNCATED = "The AI model response was truncated or invalid. The resume content may be too large. Please try with a shorter resume or contact support."
ERROR_AI_MODEL_SERVICE_ERROR = "AI model service error: {error_detail}"
ERROR_FAILED_TO_PROCESS_AI_AGENT = "Failed to process AI agent request: {error_message}"
ERROR_UNEXPECTED_ERROR = "An unexpected error occurred"

# Error Types
ERROR_TYPE_INTEGRITY_ERROR = "IntegrityError"
ERROR_TYPE_VALUE_ERROR = "ValueError"
ERROR_TYPE_DATABASE_ERROR = "DatabaseError"
ERROR_TYPE_SERVICE_ERROR = "ServiceError"
ERROR_TYPE_VALIDATION_ERROR = "ValidationError"
ERROR_TYPE_MODEL_SERVICE_ERROR = "ModelServiceError"
ERROR_TYPE_AGENT_ERROR = "AgentError"
ERROR_TYPE_INTERNAL_SERVER_ERROR = "InternalServerError"

# Success Messages
SUCCESS_SIGNED_OUT = "Signed out successfully"
SUCCESS_ACCOUNT_DELETED = "Account deleted successfully"
SUCCESS_VERIFIED_EMAIL = "Email verified successfully"
SUCCESS_RESENT_VERIFICATION_EMAIL = "Verification email resent successfully"

# Email Content
EMAIL_FROM_ADDRESS = "no-reply@wailist.com"
EMAIL_SUBJECT_VERIFY = "Verify your email"
EMAIL_VERIFICATION_BODY_TEMPLATE = """Email Verification
            Thank you for signing up! Please use the following {verification_type} to verify your email address:
            {verification_content}
            This {expiry_type} will expire in 10 minutes. If you didn't request this verification, please ignore this email.
            Best regards,
            Resumevx Team"""

# Gateway Log Messages
GATEWAY_QUEUE_TIMEOUT = "Queue timeout, ending stream"
GATEWAY_STREAM_CANCELLED = "Stream cancelled by client"
GATEWAY_ERROR_IN_STREAM = "Error in stream: {error}"
GATEWAY_ERROR_PROCESSING_INPUT_DATA = "Error processing input data: {error}"
