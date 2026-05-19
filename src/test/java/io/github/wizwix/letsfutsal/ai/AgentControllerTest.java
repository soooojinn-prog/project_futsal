package io.github.wizwix.letsfutsal.ai;

import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import io.github.wizwix.letsfutsal.dto.ProposalDTO;
import io.github.wizwix.letsfutsal.dto.UserDTO;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

class AgentControllerTest {

  private MockMvc mockMvc;
  private AgentService agentService;
  private MockHttpSession session;

  @BeforeEach
  void setUp() {
    agentService = mock(AgentService.class);
    AgentController controller = new AgentController(agentService);
    mockMvc = MockMvcBuilders.standaloneSetup(controller).build();

    session = new MockHttpSession();
    UserDTO user = new UserDTO();
    user.setUserId(1L);
    user.setNickname("수진");
    session.setAttribute("loginUser", user);
  }

  @Test
  void run_returns200WithProposal() throws Exception {
    ProposalDTO p = new ProposalDTO();
    p.setProposalId("prop_x1");
    p.setIntent("SINGLE");
    when(agentService.run(anyLong(), anyString())).thenReturn(p);

    mockMvc
        .perform(
            post("/ai/agent/run")
                .session(session)
                .contentType("application/json")
                .content("{\"userInput\":\"강남 매치\"}"))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.proposal_id").value("prop_x1"));
  }

  @Test
  void run_returns401WithoutLogin() throws Exception {
    mockMvc
        .perform(
            post("/ai/agent/run")
                .contentType("application/json")
                .content("{\"userInput\":\"매치\"}"))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void run_returns400WhenInputEmpty() throws Exception {
    mockMvc
        .perform(
            post("/ai/agent/run")
                .session(session)
                .contentType("application/json")
                .content("{\"userInput\":\"\"}"))
        .andExpect(status().isBadRequest());
  }
}
