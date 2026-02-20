library(httr2)

resp <- request("https://api.github.com/users/octocat") %>%
  req_perform()

resp_status(resp)
resp_body_json(resp)
