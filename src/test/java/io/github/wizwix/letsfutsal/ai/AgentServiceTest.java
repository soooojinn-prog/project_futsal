package io.github.wizwix.letsfutsal.ai;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.wizwix.letsfutsal.dto.ConfirmRequestDTO;
import io.github.wizwix.letsfutsal.dto.MatchProposalDTO;
import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.mapper.MatchMapper;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestTemplate;

class AgentServiceTest {

  private RestTemplate restTemplate;
  private MockRestServiceServer server;
  private MatchMapper matchMapper;
  private AgentService service;

  @BeforeEach
  void setUp() {
    restTemplate = new RestTemplate();
    server = MockRestServiceServer.createServer(restTemplate);
    matchMapper = mock(MatchMapper.class);
    service = new AgentService(restTemplate, new ObjectMapper(), matchMapper, "http://fake:8000");
  }

  @Test
  void run_parsesProposalFromPython() {
    String json =
        "{\"proposal_id\":\"prop_x1\",\"intent\":\"SINGLE\",\"warnings\":[],"
            + "\"matches\":[{\"stadium_id\":1,\"stadium_name\":\"강남\","
            + "\"start_time\":\"2026-05-23T14:00\",\"duration_min\":60,"
            + "\"team_a\":{\"id\":5,\"name\":\"A\"},\"team_b\":null,\"stage\":null}],"
            + "\"bracket\":null}";
    server
        .expect(requestTo("http://fake:8000/agent/run"))
        .andExpect(method(HttpMethod.POST))
        .andRespond(withSuccess(json, MediaType.APPLICATION_JSON));

    ProposalDTO p = service.run(1, "강남 토요일 매치");

    assertThat(p.getProposalId()).isEqualTo("prop_x1");
    assertThat(p.getIntent()).isEqualTo("SINGLE");
    assertThat(p.getMatches()).hasSize(1);
  }

  @Test
  void confirm_insertsAllMatches() {
    when(matchMapper.insertMatch(any())).thenReturn(1);

    MatchProposalDTO m1 = new MatchProposalDTO();
    m1.setStadiumId(1);
    m1.setStartTime("2026-05-23T14:00");
    MatchProposalDTO.TeamSummary t = new MatchProposalDTO.TeamSummary();
    t.setId(5);
    t.setName("A");
    m1.setTeamA(t);

    ConfirmRequestDTO req = new ConfirmRequestDTO();
    req.setProposalId("prop_x1");
    req.setMatches(List.of(m1, m1));

    List<Long> ids = service.confirm(req, 1);

    assertThat(ids).hasSize(2);
    verify(matchMapper, times(2)).insertMatch(any());
  }
}
