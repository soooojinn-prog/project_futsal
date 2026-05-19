package io.github.wizwix.letsfutsal.dto;

import java.util.List;

public class ConfirmRequestDTO {
  private String proposalId;
  private List<MatchProposalDTO> matches;

  public String getProposalId() {
    return proposalId;
  }

  public void setProposalId(String proposalId) {
    this.proposalId = proposalId;
  }

  public List<MatchProposalDTO> getMatches() {
    return matches;
  }

  public void setMatches(List<MatchProposalDTO> matches) {
    this.matches = matches;
  }
}
