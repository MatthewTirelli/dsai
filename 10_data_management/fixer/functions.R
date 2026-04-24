# functions.R
# Shared fixer helpers: Ollama /api/chat (httr2) + tool-call JSON parsing + table chunking.
# Sourced by fixer_csv.R, fixer_parcels.R, fixer_pois.R, fixer_spatial_context.R, testme.R.
# Tim Fraser

# -- Table chunking (base R only; used by batched fixer scripts) -------------------

#' Split a data.frame/tibble into consecutive row slices of size n_rows.
#' @param df Data frame or tibble.
#' @param n_rows Positive integer chunk size.
#' @return List of slices (same column structure as df).
split_df_into_row_chunks = function(df, n_rows) {
  nr = nrow(df)
  if (nr == 0L) {
    return(list())
  }
  n_rows = as.integer(n_rows)
  if (is.na(n_rows) || n_rows < 1L) {
    n_rows = 1L
  }
  starts = seq.int(1L, nr, by = n_rows)
  lapply(starts, function(s) {
    e = min(s + n_rows - 1L, nr)
    df[seq.int(s, e), , drop = FALSE]
  })
}

# -- Null coalescing (used by ollama_chat_once and truncate_tool_output) ------------

`%||%` = function(x, y) {
  if (is.null(x)) {
    y
  } else {
    x
  }
}

# -- Ollama HTTP -------------------------------------------------------------------

# Strip whitespace and a duplicated "Bearer " prefix (the client adds Bearer).
normalize_ollama_api_key = function(api_key) {
  ak = trimws(as.character(api_key %||% ""))
  if (nzchar(ak) && startsWith(tolower(ak), "bearer ")) {
    ak = trimws(substring(ak, 8L))
  }
  ak
}

# Single chat completion. Pass tools for tool-calling; pass format = "json" for JSON mode.
ollama_chat_once = function(
  base_url,
  api_key,
  model,
  messages,
  tools = NULL,
  format = NULL,
  max_output_tokens = NULL
) {
  url = paste0(sub("/$", "", base_url), "/api/chat")
  body = list(
    model = model,
    messages = messages,
    stream = FALSE
  )
  if (!is.null(tools) && length(tools) > 0L) {
    body$tools = tools
  }
  fmt = format %||% ""
  if (nzchar(as.character(fmt))) {
    body$format = as.character(fmt)
  }
  if (!is.null(max_output_tokens)) {
    body$options = list(num_predict = as.integer(max_output_tokens))
  }

  req = httr2::request(url) |>
    httr2::req_headers("Content-Type" = "application/json")
  ak = normalize_ollama_api_key(api_key)
  if (nzchar(ak)) {
    req = req |> httr2::req_headers(Authorization = paste("Bearer", ak))
  }
  req = req |>
    httr2::req_body_json(body) |>
    httr2::req_timeout(120)

  resp = httr2::req_perform(req)
  sc = httr2::resp_status(resp)
  if (sc >= 400L) {
    txt = tryCatch(httr2::resp_body_string(resp), error = function(e) "")
    msg = paste0("HTTP ", sc, " for ", url)
    if (sc == 401L) {
      msg = paste0(
        msg,
        ". Unauthorized — set OLLAMA_API_KEY in fixer/.env to a valid Ollama Cloud API key ",
        "(https://ollama.com/settings/keys). Use the raw token only; do not prefix with 'Bearer '."
      )
    } else if (sc == 403L) {
      msg = paste0(msg, ". Forbidden — the key may not have access to Ollama Cloud or this model.")
    }
    if (nzchar(txt)) {
      txt = gsub("\n", " ", txt, fixed = TRUE)
      if (nchar(txt) > 600L) {
        txt = paste0(substr(txt, 1L, 600L), "...")
      }
      msg = paste0(msg, " Response: ", txt)
    }
    stop(msg, call. = FALSE)
  }
  data = httr2::resp_body_json(resp, simplifyVector = FALSE, simplifyDataFrame = FALSE)
  msg = data$message %||% list()
  content = msg$content
  if (is.null(content)) {
    content = ""
  }
  if (!is.character(content)) {
    content = as.character(content)
  }
  content = trimws(paste(content, collapse = ""))
  list(content = content, message = msg, raw = data)
}

# -- Tool loop helpers -------------------------------------------------------------

# Parse tool function.arguments (string JSON or list) into an R list.
parse_function_arguments = function(raw) {
  if (is.null(raw)) {
    return(list())
  }
  if (is.list(raw) && !is.character(raw)) {
    return(raw)
  }
  if (is.character(raw)) {
    s = trimws(raw)
    if (!nzchar(s)) {
      return(list())
    }
    parsed = tryCatch(
      jsonlite::fromJSON(s, simplifyVector = FALSE),
      error = function(e) list()
    )
    if (is.list(parsed)) {
      return(parsed)
    }
    return(list())
  }
  list()
}

# Shorten long tool outputs for the model thread (optional).
truncate_tool_output = function(s, limit = 12000L) {
  s = as.character(s %||% "")
  if (nchar(s) <= limit) {
    return(s)
  }
  paste0(substr(s, 1L, as.integer(limit) - 30L), "\n...[truncated]")
}
