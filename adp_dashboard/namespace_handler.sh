#!/bin/bash

check_namespace_exists() {
  local namespace="$1"
  if kubectl get namespace "$namespace" &>/dev/null; then
    return 0
  else
    return 1
  fi
}

create_namespace() {
  local namespace="$1"
  kubectl create namespace "$namespace"
}

delete_namespace() {
  local namespace="$1"
  kubectl delete namespace "$namespace"
}

recreate_namespace() {
  local namespace="$1"
  if check_namespace_exists "$namespace"; then
    echo "Namespace already exists, deleting $namespace"
    delete_namespace "$namespace"
  fi
  create_namespace "$namespace"
}

main() {
  local namespace="$1"
  local delete_flag="$2"

  if [ "$delete_flag" = true ]; then
    delete_namespace "$namespace"
  else
    recreate_namespace "$namespace"
  fi
}

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <namespace> [--delete]"
  exit 1
fi

namespace="$1"
delete_flag=false

if [ "$2" = "--delete" ]; then
  delete_flag=true
fi

main "$namespace" "$delete_flag"
