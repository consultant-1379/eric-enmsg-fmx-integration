#!/bin/bash

NAMESPACE="$1"

CHECK_RESTART=$(kubectl -n ${NAMESPACE} get pods | egrep 'ImagePullBackOff|CrashLoopBackOff|Error|Pending|ErrImagePull' | awk '{print $1} {print $3}' || true)

if [ ! -z "$CHECK_RESTART" ]; then
  echo "Pod restarts detected, exiting..."

  exit 1
else
  echo "No pod restarts detected"

  exit 0
fi
