#!/usr/bin/env bash

# This script must be sourced, not run directly (e.g., 'source assume_role.sh')
if [ "${BASH_SOURCE[0]}" -ef "$0" ]; then
    echo "Error: This script must be sourced to export environment variables to your active shell."
    echo "Usage: source assume_role.sh"
    exit 1
fi

ROLE_ARN="arn:aws:iam::147997143053:role/ElvityVizUploaderRole"
PROFILE_NAME="elvity_prod"

# Unset any active temporary environment credentials to prevent session-chaining blocks
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_PROFILE

echo "Attempting to assume role: $ROLE_ARN using profile: $PROFILE_NAME..."

# Verify aws cli is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed or not in your PATH."
    return 1
fi

# Request temporary credentials from STS
TEMP_CREDS=$(AWS_PROFILE=$PROFILE_NAME aws sts assume-role \
  --role-arn "$ROLE_ARN" \
  --role-session-name gemini-safe-session \
  --query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" \
  --output text 2>&1)

# Check if the aws command succeeded
if [ $? -ne 0 ]; then
    echo "Error: Failed to assume the IAM role."
    echo "$TEMP_CREDS"
    return 1
fi

# Extract and export credentials
export AWS_ACCESS_KEY_ID=$(echo "$TEMP_CREDS" | awk '{print $1}')
export AWS_SECRET_ACCESS_KEY=$(echo "$TEMP_CREDS" | awk '{print $2}')
export AWS_SESSION_TOKEN=$(echo "$TEMP_CREDS" | awk '{print $3}')

# Export AWS_PROFILE as our clean, non-redirected profile to bypass LocalStack's default endpoint
export AWS_PROFILE="elvity_real_aws"

echo "--------------------------------------------------------"
echo "✅ Successfully assumed ElvityVizUploaderRole!"
echo "🔑 Temporary credentials exported to your current shell."
echo "⏱️  These credentials will automatically expire in 1 hour."
echo "--------------------------------------------------------"
