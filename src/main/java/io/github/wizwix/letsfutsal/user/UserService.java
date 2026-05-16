package io.github.wizwix.letsfutsal.user;

import io.github.wizwix.letsfutsal.dto.UserDTO;
import io.github.wizwix.letsfutsal.mapper.UserMapper;
import org.springframework.stereotype.Service;

@Service
public class UserService implements IUserService {
  private final UserMapper userMapper;

  public UserService(UserMapper userMapper) {
    this.userMapper = userMapper;
  }

  @Override
  public UserDTO getUserById(Long userId) {
    return userMapper.selectUserById(userId);
  }

  @Override
  public boolean isEmailExists(String email) {
    UserDTO user = userMapper.selectUserByEmail(email);
    return user != null;
  }

  @Override
  public UserDTO login(String email, String password) {
    UserDTO user = userMapper.selectUserByEmail(email);
    if (user != null && user.getPassword().equals(password)) return user;
    return null;
  }

  @Override
  public void register(UserDTO user) {
    if (user.getPreferredPosition() != null && user.getPreferredPosition().isBlank()) {
      user.setPreferredPosition(null);
    }
    // 비밀번호 암호화 추가 필요
    userMapper.insertUser(user);
  }

  @Override
  public void updateUser(UserDTO user) {
    userMapper.updateUser(user);
  }
}
