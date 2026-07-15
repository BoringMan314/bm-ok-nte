package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
	"unsafe"
)

var messageBoxW = syscall.NewLazyDLL("user32.dll").NewProc("MessageBoxW")

func fail(title, msg string) {
	text, _ := syscall.UTF16PtrFromString(msg)
	caption, _ := syscall.UTF16PtrFromString(title)
	messageBoxW.Call(0, uintptr(unsafe.Pointer(text)), uintptr(unsafe.Pointer(caption)), 0x10)
	os.Exit(1)
}

func main() {
	exe, err := os.Executable()
	if err != nil {
		fail("bm-ok-nte", "無法取得程式路徑。")
	}
	root := filepath.Dir(exe)
	pythonw := filepath.Join(root, "data", "apps", "ok-nte", "python", "pythonw.exe")
	mainPy := filepath.Join(root, "data", "apps", "ok-nte", "working", "main.py")
	working := filepath.Join(root, "data", "apps", "ok-nte", "working")

	if _, err := os.Stat(pythonw); err != nil {
		fail("bm-ok-nte", fmt.Sprintf("找不到 Python 執行檔：\n%s", pythonw))
	}
	if _, err := os.Stat(mainPy); err != nil {
		fail("bm-ok-nte", fmt.Sprintf("找不到主程式：\n%s", mainPy))
	}

	cmd := exec.Command(pythonw, mainPy)
	cmd.Dir = working
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow:    true,
		CreationFlags: syscall.CREATE_NEW_PROCESS_GROUP,
	}
	if err := cmd.Start(); err != nil {
		fail("bm-ok-nte", fmt.Sprintf("無法啟動主程式：\n%v", err))
	}
}
