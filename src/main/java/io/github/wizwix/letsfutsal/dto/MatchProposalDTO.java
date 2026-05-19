package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class MatchProposalDTO {
  @JsonProperty("stadium_id")
  private int stadiumId;

  @JsonProperty("stadium_name")
  private String stadiumName;

  @JsonProperty("start_time")
  private String startTime;

  @JsonProperty("duration_min")
  private int durationMin = 60;

  @JsonProperty("team_a")
  private TeamSummary teamA;

  @JsonProperty("team_b")
  private TeamSummary teamB;

  private String stage;

  public static class TeamSummary {
    private Integer id;
    private String name;

    public Integer getId() {
      return id;
    }

    public void setId(Integer id) {
      this.id = id;
    }

    public String getName() {
      return name;
    }

    public void setName(String name) {
      this.name = name;
    }
  }

  public int getStadiumId() {
    return stadiumId;
  }

  public void setStadiumId(int stadiumId) {
    this.stadiumId = stadiumId;
  }

  public String getStadiumName() {
    return stadiumName;
  }

  public void setStadiumName(String stadiumName) {
    this.stadiumName = stadiumName;
  }

  public String getStartTime() {
    return startTime;
  }

  public void setStartTime(String startTime) {
    this.startTime = startTime;
  }

  public int getDurationMin() {
    return durationMin;
  }

  public void setDurationMin(int durationMin) {
    this.durationMin = durationMin;
  }

  public TeamSummary getTeamA() {
    return teamA;
  }

  public void setTeamA(TeamSummary teamA) {
    this.teamA = teamA;
  }

  public TeamSummary getTeamB() {
    return teamB;
  }

  public void setTeamB(TeamSummary teamB) {
    this.teamB = teamB;
  }

  public String getStage() {
    return stage;
  }

  public void setStage(String stage) {
    this.stage = stage;
  }
}
