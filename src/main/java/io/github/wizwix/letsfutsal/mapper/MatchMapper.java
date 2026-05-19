package io.github.wizwix.letsfutsal.mapper;

import io.github.wizwix.letsfutsal.dto.MatchDTO;
import io.github.wizwix.letsfutsal.enums.Gender;
import io.github.wizwix.letsfutsal.enums.Match;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

public interface MatchMapper {
  int countIndividualPlayers(@Param("matchId") Long matchId);

  int countTeamParticipants(@Param("matchId") Long matchId);

  int insertIndividualParticipant(@Param("matchId") long matchId, @Param("userId") long userId);

  int insertMatch(@Param("match") MatchDTO match);

  int insertTeamParticipant(@Param("matchId") long matchId, @Param("teamId") long teamId);

  /// Increase or decrease a number that represents how many people are participating the match
  int modifyMatchStatus(@Param("matchId") long matchId, @Param("increment") int adjustment);

  MatchDTO selectMatchById(@Param("matchId") long matchId);

  List<MatchDTO> selectMatchList(@Param("matchType") Match matchType,
                                 @Param("region") String region,
                                 @Param("startHour") LocalTime startHour,
                                 @Param("endHour") LocalTime endHour,
                                 @Param("gender") Gender gender,
                                 @Param("minGrade") Integer minGrade,
                                 @Param("maxGrade") Integer maxGrade,
                                 @Param("status") Integer status);

  List<MatchDTO> selectMatchesByFilters(@Param("date") LocalDate date, @Param("region") String region, @Param("type") String type);

  List<MatchDTO> selectMatchesByRegionAndType(@Param("region") String region, @Param("type") String type);

  List<MatchDTO> selectUpcomingMatches();

  int updateMatchStatus(@Param("matchId") long matchId, @Param("status") int status);

  /// 특정 경기장 + 특정 날짜에 이미 잡힌 매치 목록 (에이전트 시간 슬롯 계산용)
  List<MatchDTO> selectByStadiumAndDate(
      @Param("stadiumId") long stadiumId, @Param("date") LocalDate date);

  /// 특정 팀이 [dateFrom, dateTo] 기간에 잡은 매치 목록 (에이전트 충돌 체크용)
  List<MatchDTO> selectMatchesByTeamAndDateRange(
      @Param("teamId") long teamId,
      @Param("dateFrom") LocalDate dateFrom,
      @Param("dateTo") LocalDate dateTo);
}
