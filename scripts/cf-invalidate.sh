#!/bin/bash
set -euo pipefail
PROFILE=${1:-admin}
DISTRIBUTION_ID=${2:-ESZTOMYA7BE5}
PATHS=${3:-"/*"}

AWS_PROFILE=$PROFILE aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths $PATHS | cat
