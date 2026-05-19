package io.github.wizwix.letsfutsal.dto;

import java.util.List;

public class ChatResponseDTO {
  public enum Mode {
    RAG,
    ADVICE
  }

  private String message;
  private Mode mode;
  private List<CitationDTO> citations;

  public ChatResponseDTO() {}

  public ChatResponseDTO(String message, Mode mode, List<CitationDTO> citations) {
    this.message = message;
    this.mode = mode;
    this.citations = citations;
  }

  public String getMessage() {
    return message;
  }

  public void setMessage(String message) {
    this.message = message;
  }

  public Mode getMode() {
    return mode;
  }

  public void setMode(Mode mode) {
    this.mode = mode;
  }

  public List<CitationDTO> getCitations() {
    return citations;
  }

  public void setCitations(List<CitationDTO> citations) {
    this.citations = citations;
  }
}
