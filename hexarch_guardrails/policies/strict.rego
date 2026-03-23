package policy

import future.keywords.if

default allow = false

allow if {
  input.identity.role == "admin"
}

allow if {
  input.method == "GET"
  input.path == "/health"
}
