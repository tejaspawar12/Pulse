/**
 * API response types and error handling.
 */

export interface ApiError {
  // FastAPI returns only "detail" field (string or array of validation errors)
  // status_code is NOT in JSON body (it's in HTTP status code)
  detail: string | { msg: string; type: string }[];
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}
