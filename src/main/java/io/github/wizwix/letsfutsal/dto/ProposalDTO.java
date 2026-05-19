package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class ProposalDTO {
  @JsonProperty("proposal_id")
  private String proposalId;

  private String intent;
  private List<String> warnings;
  private List<MatchProposalDTO> matches;
  private BracketDTO bracket;

  public String getProposalId() {
    return proposalId;
  }

  public void setProposalId(String proposalId) {
    this.proposalId = proposalId;
  }

  public String getIntent() {
    return intent;
  }

  public void setIntent(String intent) {
    this.intent = intent;
  }

  public List<String> getWarnings() {
    return warnings;
  }

  public void setWarnings(List<String> warnings) {
    this.warnings = warnings;
  }

  public List<MatchProposalDTO> getMatches() {
    return matches;
  }

  public void setMatches(List<MatchProposalDTO> matches) {
    this.matches = matches;
  }

  public BracketDTO getBracket() {
    return bracket;
  }

  public void setBracket(BracketDTO bracket) {
    this.bracket = bracket;
  }
}
