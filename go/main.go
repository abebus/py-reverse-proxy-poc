package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

type EchoResponse struct {
	Headers map[string][]string `json:"headers"`
	Body    json.RawMessage     `json:"body"`
}

var accessLog *os.File

func initAccessLog() error {
	var err error
	accessLog, err = os.OpenFile("access.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return fmt.Errorf("failed to open access log: %w", err)
	}
	return nil
}

func logAccess(r *http.Request, status int, duration time.Duration) {
	if accessLog == nil {
		return
	}

	logLine := fmt.Sprintf("%s [%s] %s %s %d %s\n",
		time.Now().Format("2006-01-02 15:04:05"),
		r.RemoteAddr,
		r.Method,
		r.URL.Path,
		status,
		duration,
	)

	accessLog.WriteString(logLine)
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		logAccess(r, http.StatusOK, time.Since(start))
	}()

	fmt.Fprint(w, "OK")
}

func echoJSONHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	var status int = http.StatusOK // default status

	defer func() {
		logAccess(r, status, time.Since(start))
	}()

	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
	if err != nil {
		status = http.StatusInternalServerError
		http.Error(w, "Failed to read request body", status)
		return
	}
	defer r.Body.Close()

	resp := struct {
		Headers http.Header `json:"headers"`
		Body    interface{} `json:"body"`
	}{
		Headers: r.Header,
	}

	var jsonBody interface{}
	if err := json.Unmarshal(body, &jsonBody); err == nil {
		resp.Body = jsonBody
	} else {
		resp.Body = string(body)
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(resp); err != nil {
		status = http.StatusInternalServerError
		http.Error(w, "Failed to encode response: "+err.Error(), status)
	}
}

func main() {
	if err := initAccessLog(); err != nil {
		fmt.Fprintf(os.Stderr, "Error initializing access log: %v\n", err)
		os.Exit(1)
	}
	defer accessLog.Close()

	http.HandleFunc("/", rootHandler)
	http.HandleFunc("/echo-json", echoJSONHandler)

	fmt.Println("Starting server on :9999")
	if err := http.ListenAndServe(":9999", nil); err != nil {
		fmt.Fprintf(os.Stderr, "Server failed: %v\n", err)
	}
}
