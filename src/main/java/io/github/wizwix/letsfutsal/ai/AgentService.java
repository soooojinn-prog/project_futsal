package io.github.wizwix.letsfutsal.ai;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.ConfirmRequestDTO;
import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.MatchProposalDTO;
import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.dto.TeamDTO;
import io.github.wizwix.letsfutsal.enums.Gender;
import io.github.wizwix.letsfutsal.enums.Match;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import io.github.wizwix.letsfutsal.mapper.UserMapper;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

@Service
public class AgentService {
  private static final Logger log = LoggerFactory.getLogger(AgentService.class);
  private static final int DEFAULT_MIN_GRADE = 1;
  private static final int DEFAULT_MAX_GRADE = 10;

  private final RestTemplate restTemplate;
  private final ObjectMapper objectMapper;
  private final MatchMapper matchMapper;
  private final UserMapper userMapper;
  private final String aiBaseUrl;

  @Autowired
  public AgentService(
      RestTemplate restTemplate,
      ObjectMapper objectMapper,
      MatchMapper matchMapper,
      UserMapper userMapper) {
    this(
        restTemplate,
        objectMapper,
        matchMapper,
        userMapper,
        System.getenv().getOrDefault("AI_SERVICE_URL", "http://localhost:8000"));
  }

  public AgentService(
      RestTemplate restTemplate,
      ObjectMapper objectMapper,
      MatchMapper matchMapper,
      UserMapper userMapper,
      String aiBaseUrl) {
    this.restTemplate = restTemplate;
    this.objectMapper = objectMapper;
    this.matchMapper = matchMapper;
    this.userMapper = userMapper;
    this.aiBaseUrl = aiBaseUrl;
  }

  public ProposalDTO run(long userId, String userInput) {
    Map<String, Object> body = new HashMap<>();
    body.put("user_input", userInput);
    body.put("user_id", userId);

    // 사용자가 속한 팀들을 조회해 Python에 전달 — 토너먼트 모드의 conflict 체크
    // (`find_team_conflicts`) + 자동 참가 팀 매핑에 사용된다. 팀이 없으면 team_info 생략.
    List<TeamDTO> teams = userMapper.selectTeamsByUserId(userId);
    if (teams != null && !teams.isEmpty()) {
      TeamDTO primary = teams.get(0);
      Map<String, Object> teamInfo = new HashMap<>();
      teamInfo.put("team_id", primary.getTeamId());
      teamInfo.put("team_name", primary.getTeamName());
      List<Long> teamIds = new ArrayList<>();
      Map<Long, String> teamNames = new LinkedHashMap<>();
      for (TeamDTO t : teams) {
        teamIds.add(t.getTeamId());
        teamNames.put(t.getTeamId(), t.getTeamName());
      }
      teamInfo.put("team_ids", teamIds);
      teamInfo.put("team_names", teamNames);
      body.put("team_info", teamInfo);
      log.info("Agent run: user {}의 팀 {}개 자동 매핑 (primary={})",
          userId, teams.size(), primary.getTeamId());
    } else {
      log.info("Agent run: user {}이 속한 팀이 없어 team_info 생략", userId);
    }

    try {
      return restTemplate.postForObject(
          aiBaseUrl + "/agent/run", body, ProposalDTO.class);
    } catch (Exception e) {
      log.warn("Agent /agent/run 호출 실패: {}", e.getMessage());
      throw new RuntimeException("에이전트 서비스 호출 실패", e);
    }
  }

  @Transactional
  public List<Long> confirm(ConfirmRequestDTO req, long userId) {
    List<Long> createdIds = new ArrayList<>();
    for (MatchProposalDTO p : req.getMatches()) {
      MatchDTO m = toMatchDTO(p, userId);
      int affected = matchMapper.insertMatch(m);
      if (affected > 0) {
        createdIds.add(m.getMatchId());
      }
    }
    log.info("Agent 확정 — 사용자 {} 매치 {}개 생성", userId, createdIds.size());
    return createdIds;
  }

  private MatchDTO toMatchDTO(MatchProposalDTO p, long userId) {
    LocalDateTime start = LocalDateTime.parse(p.getStartTime());
    LocalDateTime end = start.plusMinutes(p.getDurationMin());

    MatchDTO m = new MatchDTO();
    m.setStadiumId(p.getStadiumId());
    m.setRenterEntityId(userId);
    m.setMatchType(Match.TEAM);
    m.setMatchDate(start.toLocalDate());
    m.setStartHour(start.toLocalTime());
    m.setEndHour(end.toLocalTime());
    m.setGender(Gender.BOTH);
    m.setMinGrade(DEFAULT_MIN_GRADE);
    m.setMaxGrade(DEFAULT_MAX_GRADE);
    m.setStatus(0);
    return m;
  }
}
