package policy

import future.keywords.if

default allow = false

allow if {
  input.path == "/health"
}

allow if {
  input.path == "/docs"
}

allow if {
  input.path == "/openapi.json"
}

allow if {
  input.path == "/redoc"
}

allow if {
  input.identity.role == "admin"
}
