package io.github.wizwix.letsfutsal.dto;

import java.util.List;
import java.util.Map;

public class BracketDTO {
  private List<List<Map<String, Object>>> rounds;

  public List<List<Map<String, Object>>> getRounds() {
    return rounds;
  }

  public void setRounds(List<List<Map<String, Object>>> rounds) {
    this.rounds = rounds;
  }
}
