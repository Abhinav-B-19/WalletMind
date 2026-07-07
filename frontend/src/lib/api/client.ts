import axios from "axios";

const DEFAULT_API_BASE_URL = (() => {
  if (typeof window !== "undefined" && window.location?.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
})();

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export class ApiClientError extends Error {
  code?: string;
  status?: number;
  details?: unknown;

  constructor(
    message: string,
    options?: {
      code?: string;
      status?: number;
      details?: unknown;
    },
  ) {
    super(message);
    this.name = "ApiClientError";
    this.code = options?.code;
    this.status = options?.status;
    this.details = options?.details;
  }
}

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 90000,
  withCredentials: true,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const code = error.response?.data?.code;
    const status = error.response?.status;
    const details = error.response?.data?.details;
    const message =
      error.response?.data?.message ??
      error.message ??
      "Request failed. Please try again.";

    return Promise.reject(
      new ApiClientError(message, {
        code,
        status,
        details,
      }),
    );
  },
);
