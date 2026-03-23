package policy

import future.keywords.if

default allow = true

allow = false if {
  startswith(input.path, "/admin")
  input.identity.role != "admin"
}
