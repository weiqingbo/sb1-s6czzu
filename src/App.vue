<template>
  <div class="container">
    <div class="leftBox" id="leftBox">
      <img :src="leftBoxImage" alt="Left Image" id="leftBox_img" />
    </div>
    <div class="rightBox" id="rightBox">
      <div id="preview-container" v-if="!showEditContainer">
        <h1 style="text-align: center">AI智能生成简历</h1>
        <form id="resumeForm" @submit.prevent="generateResume">
          <div class="form-group" v-for="field in formFields" :key="field.id">
            <label :for="field.id" :class="{ short: field.short }">{{ field.label }}</label>
            <input :type="field.type" :id="field.id" :name="field.id" v-model="formData[field.id]" required />
          </div>
          <div class="form-group file">
            <label for="avatar">上传图片</label>
            <div class="userdefined-file">
              <input type="text" name="userdefinedFile" id="userdefinedFile" :value="avatarFileName" readonly>
              <button type="button" @click="triggerFileInput">上传</button>
            </div>
            <input type="file" name="avatar" id="avatar" @change="handleFileChange" ref="fileInput">
          </div>
          <div class="form-group">
            <button type="submit" id="submit">生成简历</button>
          </div>
        </form>

        <div id="message" class="message" :class="messageClass" v-if="message">{{ message }}</div>
        <div class="progress" id="progress" v-show="showProgress">
          <div class="progress-bar" id="progressBar"></div>
        </div>

        <div class="form-group" id="edit-resume" v-if="showEditResume">
          <button id="edit-button" @click="showEditContainer = true">个性化修改简历</button>
        </div>

        <div id="downloadLink" class="center-link">
          <a v-if="downloadUrl" :href="downloadUrl" download="简历.pdf">点击下载简历</a>
        </div>
      </div>

      <div id="edit-container" v-else>
        <div style="height: 50px;">
          <a id="resume-button" style="font-size: 14px; color: #939393;margin-left: 8px;" @click="showEditContainer = false">
            &lt;返回</a>
          <h2 style="display: inline-block;margin-top: 0;margin-left: 65px;">个性化修改简历</h2>
        </div>
        <form id="edit-form" @submit.prevent="editResume">
          <div id="chat-box">
            <div v-for="(msg, index) in chatMessages" :key="index" class="message" :class="msg.type">
              <div v-if="msg.type === 'question'" class="avatar-container left">
                <img :src="botAvatar" class="avatar" alt="Bot Avatar">
              </div>
              <span class="text">{{ msg.text }}</span>
              <div v-if="msg.type === 'answer'" class="avatar-container right">
                <img :src="userAvatar" class="avatar" alt="User Avatar">
              </div>
            </div>
          </div>
          <div id="input-container">
            <textarea id="answer-input" rows="2" cols="50" v-model="editContent"></textarea>
            <button type="submit">发送</button>
          </div>

          <div id="edit-message" class="message" :class="editMessageClass" v-if="editMessage">{{ editMessage }}</div>
          <div class="progress" id="edit-progress" v-show="showEditProgress">
            <div class="progress-bar" id="edit-progressBar"></div>
          </div>
          <div id="edit-downloadLink" class="center-link">
            <a v-if="editDownloadUrl" :href="editDownloadUrl" download="修改后的简历.pdf">点击下载修改后的简历</a>
          </div>
        </form>
      </div>
    </div>
    <div class="pdf-container" id="pdfContainer">
      <embed v-if="pdfUrl" :src="pdfUrl" type="application/pdf" width="100%" height="100%">
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      formFields: [
        { id: 'name', label: '姓名', type: 'text', short: true },
        { id: 'email', label: '邮箱', type: 'email', short: true },
        { id: 'phone', label: '联系方式', type: 'text' },
        { id: 'location', label: '地址', type: 'text', short: true },
        { id: 'job_position', label: '应聘岗位', type: 'text' },
        { id: 'specialty', label: '专业', type: 'text', short: true },
      ],
      formData: {
        name: '',
        email: '',
        phone: '',
        location: '',
        job_position: '',
        specialty: '',
      },
      avatarFile: null,
      avatarFileName: '未选择任何文件',
      message: '',
      messageClass: '',
      showProgress: false,
      showEditResume: false,
      downloadUrl: '',
      showEditContainer: false,
      editContent: '',
      editMessage: '',
      editMessageClass: '',
      showEditProgress: false,
      editDownloadUrl: '',
      chatMessages: [],
      pdfUrl: '',
      leftBoxImage: 'https://airesume.oss-cn-beijing.aliyuncs.com/%E5%B7%A6%E4%BE%A7%E5%9B%BE%E7%89%87.png?Expires=1729350237&OSSAccessKeyId=TMP.3Kji3uPFnmCjh65syDfkmPtiNfUeGSgCEsLpqoQ5CEKFQdJAkzqXfg7ukQmNZf4xsssP9sHvkKyWaDjFB7AhZyZUh3iPC7&Signature=BDu%2BU%2FyYHYrtN2vUROIQ%2Fm%2FdyfY%3D',
      botAvatar: 'https://airesume.oss-cn-beijing.aliyuncs.com/bot.png?Expires=1729350188&OSSAccessKeyId=TMP.3Kji3uPFnmCjh65syDfkmPtiNfUeGSgCEsLpqoQ5CEKFQdJAkzqXfg7ukQmNZf4xsssP9sHvkKyWaDjFB7AhZyZUh3iPC7&Signature=VrOIGZQMAl4thVcWMK5UWev5UNY%3D',
      userAvatar: 'https://airesume.oss-cn-beijing.aliyuncs.com/yonghu.png?Expires=1729350211&OSSAccessKeyId=TMP.3Kji3uPFnmCjh65syDfkmPtiNfUeGSgCEsLpqoQ5CEKFQdJAkzqXfg7ukQmNZf4xsssP9sHvkKyWaDjFB7AhZyZUh3iPC7&Signature=EUjRzkf3NckM4tOkOXItDCxdwQQ%3D',
    };
  },
  mounted() {
    this.addMessage("欢迎进行个性化修改简历，您可以根据您的特点来个性化修改简历", 'question');
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    handleFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.avatarFile = file;
        this.avatarFileName = file.name;
      }
    },
    async generateResume() {
      this.message = "简历正在制作中...";
      this.messageClass = '';
      this.showProgress = true;

      const formData = new FormData();
      for (const key in this.formData) {
        formData.append(key, this.formData[key]);
      }
      if (this.avatarFile) {
        formData.append("avatar", this.avatarFile);
      }

      try {
        const response = await axios.post("http://127.0.0.1:5000/generate_resume", formData, {
          responseType: 'blob'
        });

        this.showProgress = false;
        this.message = "简历生成成功！";
        this.messageClass = "success";
        this.showEditResume = true;

        const blob = new Blob([response.data], { type: 'application/pdf' });
        this.downloadUrl = URL.createObjectURL(blob);
        this.pdfUrl = this.downloadUrl;
      } catch (error) {
        this.showProgress = false;
        this.message = "An error occurred";
        this.messageClass = "error";
        console.error('Error generating resume:', error);
      }
    },
    async editResume() {
      this.addMessage(this.editContent, 'answer');
      this.addMessage("简历正在修改中...", 'question');
      this.showEditProgress = true;

      const data = {
        ...this.formData,
        content: this.editContent,
      };

      try {
        const response = await axios.post('http://127.0.0.1:5000/edit_resume', data, {
          responseType: 'blob'
        });

        this.showEditProgress = false;
        this.addMessage("已经根据您的需求个性化修改简历！您可以通过两侧的简历来看个性化简历修改的效果", 'question');

        const blob = new Blob([response.data], { type: 'application/pdf' });
        this.editDownloadUrl = URL.createObjectURL(blob);
        this.pdfUrl = this.editDownloadUrl;
      } catch (error) {
        this.showEditProgress = false;
        this.editMessage = "An error occurred while editing the resume";
        this.editMessageClass = "error";
        console.error('Error editing resume:', error);
      }

      this.editContent = '';
    },
    addMessage(text, type) {
      this.chatMessages.push({ text, type });
      this.$nextTick(() => {
        const chatBox = this.$el.querySelector('#chat-box');
        chatBox.scrollTop = chatBox.scrollHeight;
      });
    },
  },
  watch: {
    showEditContainer(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          const leftBox = this.$el.querySelector('#leftBox');
          leftBox.style.width = '33%';
          leftBox.style.height = '520px';
          leftBox.style.marginTop = '80px';
          this.$el.querySelector('#rightBox').style.width = '34%';
        });
      } else {
        this.$nextTick(() => {
          const leftBox = this.$el.querySelector('#leftBox');
          leftBox.style.width = '28%';
          leftBox.style.height = '670px';
          leftBox.style.marginTop = '0px';
          this.$el.querySelector('#rightBox').style.width = '39%';
        });
      }
    }
  }
};
</script>

<style>
body {
  font-family: Arial, sans-serif;
  margin: 0;
  padding: 0;
  background-color: #f0f0f0;
}
.container {
  overflow: hidden;
  max-width: 1200px;
  margin: 60px auto 0;
  background: white;
  border-radius: 10px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  display: flex;
  margin-top: 80px;
}
.container .leftBox {
  width: 28%;
  height: 670px;
}
.leftBox img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.container .rightBox {
  width: 39%;
  height: 670px;
  background-color: #e8f3ff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.form-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  color: #555;
}
.form-group label {
  display: block;
  width: 80px;
  font-size: 18px;
  margin-right: 5px;
  margin-bottom: 4px;
}
.form-group input,
.form-group button {
  flex: auto;
  padding: 10px;
  font-size: 16px;
  border-radius: 8px;
  border: 1px solid #E5E5E5;
}
.form-group button {
  background-color: rgb(0, 104, 249);
  color: white;
  cursor: pointer;
  border: none;
}
.form-group button:hover {
  background-color: #aa00ff;
}
.message {
  margin-top: 20px;
  padding: 10px;
  border-radius: 4px;
  display: none;
  text-align: center;
}
.message.success {
  background-color: #d4edda;
  color: #155724;
  border-radius: 8px;
}
.message.error {
  background-color: #f8d7da;
  color: #721c24;
  border-radius: 8px;
}
.progress {
  width: 80%;
  background-color: #f3f3f3;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 10px;
  display: none;
  margin-left: 40px;
}
.progress-bar {
  width: 0;
  height: 10px;
  background-color: #28a745;
  animation: progress-animation 150s infinite;
}
@keyframes progress-animation {
  0% {
    width: 0;
  }
  100% {
    width: 100%;
  }
}
.center-link {
  text-align: center;
  margin-top: 10px;
  text-decoration: none;
}
.center-link a {
  color: black;
  text-decoration: none;
}
.short {
  letter-spacing: 22px;
}
.file {
  position: relative;
  height: 40px;
  line-height: 40px;
}
.file label {
  display: inline-block;
}
.userdefined-file {
  position: absolute;
  top: 0;
  left: 84px;
  z-index: 2;
  width: 342px;
  height: 40px;
  line-height: 40px;
  font-size: 0;
}
.userdefined-file input[type="text"] {
  color: #d0d0d0;
  display: inline-block;
  vertical-align: middle;
  padding-right: 14px;
  padding-left: 14px;
  width: 342px;
  box-sizing: border-box;
  border: 1px solid #E5E5E5;
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.userdefined-file button {
  position: absolute;
  right: 0;
  display: inline-block;
  vertical-align: middle;
  width: 80px;
  text-align: center;
  height: 40px;
  font-size: 14px;
  background-color: #0068f9;
  border: none;
  color: #fff;
  cursor: pointer;
}
.file input[type="file"] {
  z-index: 3;
  opacity: 0;
  width: 320px;
  height: 40px;
  line-height: 40px;
  cursor: pointer;
}
#submit {
  font-weight: 700;
}
input:focus {
  outline: none;
  border: 1px solid #bababa;
}
.pdf-container {
  width: 33%;
  height: 520px;
  margin-top: 80px;
}
#chat-box {
  padding: 4px;
  width: 95%;
  height: 460px;
  overflow-y: scroll;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  margin-left: 8px;
  border-radius: 8px;
}

#chat-box::-webkit-scrollbar {
  width: 0px;
}

#chat-box::-webkit-scrollbar-track {
  background-color: white;
}

#chat-box::-webkit-scrollbar-thumb {
  background-color: white;
  border-radius: 8px;
}

#chat-box::-webkit-scrollbar-thumb:hover {
  background-color: white;
}

#input-container {
  width: 100%;
  justify-content: space-evenly;
  margin-top: auto;
  display: flex;
  flex-direction: row;
  background-color: #f2f2f2;
}

#input-container button {
  width: 12%;
  height: 40px;
  font-size: 18px;
  font-weight: 500;
  color: #fff;
  border-radius: 8px;
  border: 0;
  background-color: #0068f9;
  opacity: 0.8;
  margin-top: 5px;
}
#answer-input {
  width: 81%;
  margin-top: 6px;
  margin-bottom: 4px;
  height: 34px;
  border: 0;
  border-radius: 5px;
  background-color: #fff;
  resize: none;
  font-size: 16px;
}

#answer-input:focus {
  outline: none;
  line-height: 34px;
  text-indent: 4px;
  color: #555;
  font-weight: 300;
}

.message {
  display: flex;
  margin: 10px 0;
}
.message.question {
  justify-content: flex-start;
}
.message.answer {
  justify-content: flex-end;
}
.text {
  max-width: 60%;
  padding: 10px;
  border-radius: 10px;
  word-wrap: break-word;
}
.question .text {
  background-color: #e8f3ff;
  line-height: 26px;
  color: #383838;
  text-align: justify;
}
.answer .text {
  background-color: #5eabff;
  line-height: 26px;
  text-align: justify;
  opacity: 0.7;
}
.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
}

.avatar-container {
  display: flex;
  align-items: flex-start;
}

.avatar-container.left {
  margin-right: 10px;
}

.avatar-container.right {
  margin-left: 10px;
}
</style>