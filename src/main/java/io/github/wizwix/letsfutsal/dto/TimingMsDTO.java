package io.github.wizwix.letsfutsal.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class TimingMsDTO {
  @JsonProperty("frame_extract")
  private int frameExtract;

  private int mediapipe;
  private int classify;
  private int feedback;
  private int total;

  public int getFrameExtract() {
    return frameExtract;
  }

  public void setFrameExtract(int v) {
    this.frameExtract = v;
  }

  public int getMediapipe() {
    return mediapipe;
  }

  public void setMediapipe(int v) {
    this.mediapipe = v;
  }

  public int getClassify() {
    return classify;
  }

  public void setClassify(int v) {
    this.classify = v;
  }

  public int getFeedback() {
    return feedback;
  }

  public void setFeedback(int v) {
    this.feedback = v;
  }

  public int getTotal() {
    return total;
  }

  public void setTotal(int v) {
    this.total = v;
  }
}
