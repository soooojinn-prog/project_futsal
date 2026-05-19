package io.github.wizwix.letsfutsal.ai;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.dto.StadiumDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import io.github.wizwix.letsfutsal.mapper.StadiumMapper;
import io.github.wizwix.letsfutsal.mapper.TeamMapper;
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

  /** 지역으로 경기장 검색. region 비어있으면 전체 반환. */
  @GetMapping("/stadium")
  public List<StadiumDTO> searchStadium(
      @RequestParam(required = false) String region,
      @RequestParam(required = false) String dateFrom,
      @RequestParam(required = false) String dateTo) {
    if (region == null || region.isBlank()) {
      return stadiumMapper.selectAllStadiums();
    }
    return stadiumMapper.selectStadiumsByRegion(region);
  }

  /** 경기장 + 날짜에 빈 1시간 슬롯(9~23시 중) 목록 반환. */
  @GetMapping("/stadium/{id}/slots")
  public List<Map<String, String>> listStadiumSlots(
      @PathVariable("id") long stadiumId, @RequestParam("date") String date) {
    LocalDate d = LocalDate.parse(date);
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
}
