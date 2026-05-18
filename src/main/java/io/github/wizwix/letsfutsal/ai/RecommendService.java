package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import io.github.wizwix.letsfutsal.match.MatchService;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

@Service
public class RecommendService {
  private final RestTemplate restTemplate;
  private final MatchService matchService;
  private final String aiServiceUrl;

  public RecommendService(RestTemplate restTemplate, MatchService matchService) {
    this.restTemplate = restTemplate;
    this.matchService = matchService;
    this.aiServiceUrl = System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000");
  }

  public List<MatchDTO> getRecommendedMatches(UserDTO user) {
    try {
      Map<String, Object> request = Map.of(
          "userId", user.getUserId(),
          "preferredPosition", user.getPreferredPosition() != null ? user.getPreferredPosition() : "FW",
          "gender", user.getGender() != null ? user.getGender().name() : "ALL",
          "grade", user.getGrade());

      @SuppressWarnings("unchecked")
      Map<String, Object> response = restTemplate.postForObject(
          aiServiceUrl + "/recommend/matches", request, Map.class);

      if (response == null || !response.containsKey("matchIds")) {
        return getFallbackMatches();
      }

      @SuppressWarnings("unchecked")
      List<Integer> matchIds = (List<Integer>) response.get("matchIds");
      return matchIds.stream()
          .map(id -> matchService.getMatchById(id.longValue()))
          .filter(m -> m != null && m.getStatus() < 10)
          .limit(6)
          .toList();
    } catch (Exception e) {
      return getFallbackMatches();
    }
  }

  private List<MatchDTO> getFallbackMatches() {
    return matchService.getMatchList("all", null, null, null, null, null, null, null)
        .stream()
        .filter(m -> m.getStatus() < 10)
        .limit(6)
        .toList();
  }
}
