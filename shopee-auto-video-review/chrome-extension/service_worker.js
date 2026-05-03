chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      alert("Prototype: เปิดโหมดช่วยกรอกฟอร์มแล้ว กรุณาตรวจสอบก่อนกดยืนยันทุกครั้ง");
    },
  });
});
