package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.StadiumDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import io.github.wizwix.letsfutsal.mapper.StadiumMapper;
import io.github.wizwix.letsfutsal.mapper.TeamMapper;
import jakarta.servlet.http.HttpServletRequest;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * LangGraph 에이전트(Python) 호출용 read-only API. 인터셉터 영향 없음 (현재 LoginInterceptor 미등록).
 */
@RestController
@RequestMapping("/api/agent-data")
public class AgentDataController {

  private static final LocalTime OPEN_HOUR = LocalTime.of(9, 0);
  private static final LocalTime CLOSE_HOUR = LocalTime.of(23, 0);

  private final StadiumMapper stadiumMapper;
  private final MatchMapper matchMapper;
  private final TeamMapper teamMapper;

  public AgentDataController(
      StadiumMapper stadiumMapper, MatchMapper matchMapper, TeamMapper teamMapper) {
    this.stadiumMapper = stadiumMapper;
    this.matchMapper = matchMapper;
    this.teamMapper = teamMapper;
  }

  /**
   * 검색어로 경기장 검색. region 또는 name 양쪽 부분일치 (LLM이 "강남" 추출했을 때 광역 region이 "서울"이라도 stadium name이 "강남구장"이면 매치).
   * region 비어있으면 전체 반환. Python Tool 호환 위해 {id, name, region}만 추출.
   *
   * <p>region을 raw query string에서 직접 추출 + UTF-8 percent-decode — Tomcat URI 인코딩 환경에 무관.
   */
  @GetMapping("/stadium")
  public List<Map<String, Object>> searchStadium(HttpServletRequest request) {
    String region = extractQueryParam(request.getQueryString(), "region");
    List<StadiumDTO> raw = stadiumMapper.selectAllStadiums();
    String q = region == null ? "" : region.trim();
    List<Map<String, Object>> out = new ArrayList<>();
    for (StadiumDTO s : raw) {
      if (!q.isEmpty()
          && !(s.getRegion() != null && s.getRegion().contains(q))
          && !(s.getName() != null && s.getName().contains(q))) {
        continue;
      }
      Map<String, Object> m = new HashMap<>();
      m.put("id", s.getStadiumId());
      m.put("name", s.getName());
      m.put("region", s.getRegion());
      out.add(m);
    }
    return out;
  }

  /** 경기장 + 날짜에 빈 1시간 슬롯(9~23시 중) 목록 반환. date 비어있으면 오늘 기준. */
  @GetMapping("/stadium/{id}/slots")
  public List<Map<String, String>> listStadiumSlots(
      @PathVariable("id") long stadiumId,
      @RequestParam(value = "date", required = false) String date) {
    LocalDate d;
    try {
      d = (date == null || date.isBlank()) ? LocalDate.now() : LocalDate.parse(date);
    } catch (Exception e) {
      d = LocalDate.now();
    }
    List<MatchDTO> booked = matchMapper.selectByStadiumAndDate(stadiumId, d);

    List<Map<String, String>> slots = new ArrayList<>();
    for (int hour = OPEN_HOUR.getHour(); hour < CLOSE_HOUR.getHour(); hour++) {
      LocalTime start = LocalTime.of(hour, 0);
      LocalTime end = start.plusHours(1);
      boolean conflict = false;
      for (MatchDTO m : booked) {
        if (m.getStartHour() == null) continue;
        LocalTime ms = m.getStartHour();
        LocalTime me = m.getEndHour() != null ? m.getEndHour() : ms.plusHours(1);
        if (!(end.compareTo(ms) <= 0 || start.compareTo(me) >= 0)) {
          conflict = true;
          break;
        }
      }
      if (!conflict) {
        Map<String, String> slot = new HashMap<>();
        slot.put("start", d.atTime(start).toString());
        slot.put("end", d.atTime(end).toString());
        slots.add(slot);
      }
    }
    return slots;
  }

  @GetMapping("/team-members/{teamId}")
  public List<UserDTO> teamMembers(@PathVariable long teamId) {
    return teamMapper.selectMembersByTeamId(teamId);
  }

  @GetMapping("/team-conflicts/{teamId}")
  public List<MatchDTO> teamConflicts(
      @PathVariable long teamId,
      @RequestParam("dateFrom") String dateFrom,
      @RequestParam("dateTo") String dateTo) {
    return matchMapper.selectMatchesByTeamAndDateRange(
        teamId, LocalDate.parse(dateFrom), LocalDate.parse(dateTo));
  }

  /** raw query string에서 특정 키의 값을 percent-decode하여 반환. Tomcat URI 인코딩 무관. */
  private static String extractQueryParam(String queryString, String key) {
    if (queryString == null || queryString.isEmpty()) return null;
    String prefix = key + "=";
    for (String pair : queryString.split("&")) {
      if (pair.startsWith(prefix)) {
        String raw = pair.substring(prefix.length());
        try {
          return URLDecoder.decode(raw, StandardCharsets.UTF_8);
        } catch (Exception e) {
          return raw;
        }
      }
    }
    return null;
  }
}
