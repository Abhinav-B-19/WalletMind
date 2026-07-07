import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GeminiApiKeyManager } from "@/features/ai-key/gemini-api-key-manager";
import * as aiKeyApi from "@/lib/api/ai-key";

vi.mock("@/lib/api/ai-key", () => ({
  getGeminiKeyStatus: vi.fn(),
  getGeminiApiKeyForReveal: vi.fn(),
  setGeminiApiKey: vi.fn(),
  deleteGeminiApiKey: vi.fn(),
}));

describe("GeminiApiKeyManager", () => {
  const renderInRouter = (ui: ReactElement) =>
    render(<MemoryRouter>{ui}</MemoryRouter>);

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: false,
      masked_key: null,
      source: "none",
      model: "gemini-2.5-flash",
      last_validated: null,
    });
    vi.mocked(aiKeyApi.getGeminiApiKeyForReveal).mockResolvedValue({
      configured: true,
      source: "session",
      api_key: "AIzarevealedsessionkey12345",
    });
    vi.mocked(aiKeyApi.setGeminiApiKey).mockResolvedValue();
    vi.mocked(aiKeyApi.deleteGeminiApiKey).mockResolvedValue();
  });

  it("shows first-time configuration state with Save and no Validate button", async () => {
    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    expect(input.type).toBe("password");
    expect(input.placeholder).toBe("Paste your Gemini API key");
    expect(
      screen.getByText("Use a Gemini credential starting with AIza or AQ."),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Get API Key" })).toHaveAttribute(
      "href",
      "https://aistudio.google.com/app/apikey",
    );
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Validate" }),
    ).not.toBeInTheDocument();
  });

  it("loads existing configured key as masked by default", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AIzaAb********************Wls0WA",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });

    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    expect(input.type).toBe("password");
    expect(input.value).toBe("AIzaAb********************Wls0WA");
    expect(screen.getByText("Configured")).toBeInTheDocument();
    expect(screen.getByText("session")).toBeInTheDocument();
  });

  it("reveals and re-masks existing session key with eye toggle", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AIzaAb********************Wls0WA",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });

    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;

    fireEvent.click(screen.getByRole("button", { name: "Show API key" }));
    await waitFor(() => {
      expect(aiKeyApi.getGeminiApiKeyForReveal).toHaveBeenCalled();
    });
    expect(input.type).toBe("text");
    expect(input.value).toBe("AIzarevealedsessionkey12345");

    fireEvent.click(screen.getByRole("button", { name: "Hide API key" }));
    expect(input.type).toBe("password");
    expect(input.value).toBe("AIzaAb********************Wls0WA");
  });

  it("saves key with automatic backend validation", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus)
      .mockResolvedValueOnce({
        configured: false,
        masked_key: null,
        source: "none",
        model: "gemini-2.5-flash",
        last_validated: null,
      })
      .mockResolvedValueOnce({
        configured: true,
        masked_key: "AQsave*******************12345",
        source: "session",
        model: "gemini-2.5-flash",
        last_validated: "2026-07-07T01:02:03Z",
      });

    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    fireEvent.change(input, {
      target: { value: "AIza-test-key-with-minimum-length-123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(aiKeyApi.setGeminiApiKey).toHaveBeenCalledWith(
        "AIza-test-key-with-minimum-length-123",
      );
    });

    expect(await screen.findByText("Configured")).toBeInTheDocument();
    expect(screen.getByText("session")).toBeInTheDocument();
    expect(input.value).toBe("AQsave*******************12345");
    expect(aiKeyApi.getGeminiKeyStatus).toHaveBeenCalledTimes(2);
  });

  it("normalizes quoted AIza keys before saving", async () => {
    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    fireEvent.change(input, {
      target: { value: '  "AIza-quoted-key-accepted-123456"  ' },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(aiKeyApi.setGeminiApiKey).toHaveBeenCalledWith(
        "AIza-quoted-key-accepted-123456",
      );
    });
  });

  it("accepts AQ authorization keys", async () => {
    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    fireEvent.change(input, {
      target: { value: "AQ-new-google-auth-key-12345" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => {
      expect(aiKeyApi.setGeminiApiKey).toHaveBeenCalledWith(
        "AQ-new-google-auth-key-12345",
      );
    });
  });

  it("shows persistent home success banner when key is configured", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AQhome*******************12345",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });

    renderInRouter(<GeminiApiKeyManager context="home" hideWhenConfigured />);

    expect(
      await screen.findByText("AI Configuration Complete"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open AI Settings" }),
    ).toHaveAttribute("href", "/app/settings?section=ai");
    expect(
      screen.queryByLabelText("Gemini API Key (Google AI Studio)"),
    ).not.toBeInTheDocument();
  });

  it("emits update success notification in settings context", async () => {
    const onNotification = vi.fn();

    vi.mocked(aiKeyApi.getGeminiKeyStatus)
      .mockResolvedValueOnce({
        configured: true,
        masked_key: "AQold*******************12345",
        source: "session",
        model: "gemini-2.5-flash",
        last_validated: "2026-07-07T01:02:03Z",
      })
      .mockResolvedValueOnce({
        configured: true,
        masked_key: "AQnew*******************67890",
        source: "session",
        model: "gemini-2.5-flash",
        last_validated: "2026-07-07T01:02:03Z",
      });

    render(
      <MemoryRouter>
        <GeminiApiKeyManager
          context="settings"
          onNotification={onNotification}
        />
      </MemoryRouter>,
    );

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "AQ-updated-auth-key-12345" } });
    fireEvent.click(screen.getByRole("button", { name: "Update Key" }));

    await waitFor(() => {
      expect(onNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: "success",
          title: "API Key Updated Successfully",
          autoDismissMs: 5000,
        }),
      );
    });

    expect(
      screen.queryByText("Gemini API key updated successfully."),
    ).not.toBeInTheDocument();
  });

  it("emits removal notification in settings context", async () => {
    const onNotification = vi.fn();
    vi.mocked(aiKeyApi.getGeminiKeyStatus)
      .mockResolvedValueOnce({
        configured: true,
        masked_key: "AQMask********************Tail",
        source: "session",
        model: "gemini-2.5-flash",
        last_validated: "2026-07-07T01:02:03Z",
      })
      .mockResolvedValueOnce({
        configured: false,
        masked_key: null,
        source: "none",
        model: "gemini-2.5-flash",
        last_validated: null,
      });

    render(
      <MemoryRouter>
        <GeminiApiKeyManager
          context="settings"
          onNotification={onNotification}
        />
      </MemoryRouter>,
    );

    await screen.findByLabelText("Gemini API Key (Google AI Studio)");
    fireEvent.click(screen.getByRole("button", { name: "Remove Key" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(onNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: "warning",
          title: "API Key Removed",
          autoDismissMs: 5000,
        }),
      );
    });
  });

  it("emits error notification and keeps previous key when update fails", async () => {
    const onNotification = vi.fn();
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AQOld********************Key123",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });
    vi.mocked(aiKeyApi.setGeminiApiKey).mockRejectedValue(new Error("invalid"));

    render(
      <MemoryRouter>
        <GeminiApiKeyManager
          context="settings"
          onNotification={onNotification}
        />
      </MemoryRouter>,
    );

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "AQ-invalid-key" } });
    fireEvent.click(screen.getByRole("button", { name: "Update Key" }));

    await waitFor(() => {
      expect(onNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          variant: "error",
          title: "Unable to Update API Key",
        }),
      );
    });
    expect(input.value).toBe("AQOld********************Key123");
  });

  it("keeps previous valid key when replacement validation fails", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AIzaOld********************Key123",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });
    vi.mocked(aiKeyApi.setGeminiApiKey).mockRejectedValue(new Error("invalid"));

    renderInRouter(<GeminiApiKeyManager context="home" />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    expect(input.value).toBe("AIzaOld********************Key123");

    fireEvent.change(input, { target: { value: "AIza-new-invalid-key" } });
    fireEvent.click(screen.getByRole("button", { name: "Update Key" }));

    expect(await screen.findByText("invalid")).toBeInTheDocument();
    expect(input.value).toBe("AIzaOld********************Key123");
  });

  it("blocks malformed credentials before backend call", async () => {
    renderInRouter(<GeminiApiKeyManager context="home" />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    fireEvent.change(input, { target: { value: "not-a-gemini-credential" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(
      await screen.findByText(
        "This doesn't appear to be a supported Gemini credential.",
      ),
    ).toBeInTheDocument();
    expect(aiKeyApi.setGeminiApiKey).not.toHaveBeenCalled();
  });

  it("removes key with confirmation dialog", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AIzaAb********************Wls0WA",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });

    renderInRouter(<GeminiApiKeyManager />);

    await screen.findByLabelText("Gemini API Key (Google AI Studio)");
    fireEvent.click(screen.getByRole("button", { name: "Remove Key" }));
    expect(
      screen.getByText("Remove your configured Gemini API key?"),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => {
      expect(aiKeyApi.deleteGeminiApiKey).toHaveBeenCalled();
    });
  });

  it("renders stored masked key for configured session state", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AIzaMask********************Tail",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });

    renderInRouter(<GeminiApiKeyManager />);

    const input = (await screen.findByLabelText(
      "Gemini API Key (Google AI Studio)",
    )) as HTMLInputElement;
    expect(input.value).toBe("AIzaMask********************Tail");
  });

  it("shows setup form on home when key is not configured", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: false,
      masked_key: null,
      source: "none",
      model: "gemini-2.5-flash",
      last_validated: null,
    });

    renderInRouter(<GeminiApiKeyManager context="home" hideWhenConfigured />);

    expect(
      await screen.findByLabelText("Gemini API Key (Google AI Studio)"),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("AI Configuration Complete"),
    ).not.toBeInTheDocument();
  });

  it("hides home setup form when key is already configured", async () => {
    vi.mocked(aiKeyApi.getGeminiKeyStatus).mockResolvedValue({
      configured: true,
      masked_key: "AIzaMask********************Tail",
      source: "session",
      model: "gemini-2.5-flash",
      last_validated: "2026-07-07T01:02:03Z",
    });

    renderInRouter(<GeminiApiKeyManager context="home" hideWhenConfigured />);

    await waitFor(() => {
      expect(
        screen.queryByText("Configure Gemini API Key"),
      ).not.toBeInTheDocument();
    });
  });
});
