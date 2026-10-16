/* Read the target exec image's RSS at its exit stop, before mm teardown.
 * Kept out of timed runs: ptrace adds overhead and must not affect wall/CPU.
 * Linux wait4 ru_maxrss retains pre-exec launcher high-water marks.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static unsigned long long read_kib(pid_t pid, const char *file, const char *key) {
    char path[128], line[512];
    snprintf(path, sizeof path, "/proc/%ld/%s", (long)pid, file);
    FILE *stream = fopen(path, "r");
    if (!stream) return 0;
    unsigned long long value = 0;
    while (fgets(line, sizeof line, stream)) {
        if (!strncmp(line, key, strlen(key))) {
            value = strtoull(line + strlen(key), NULL, 10);
            break;
        }
    }
    fclose(stream);
    return value;
}

static int wait_child(pid_t pid, int *status) {
    pid_t result;
    do { result = waitpid(pid, status, 0); } while (result < 0 && errno == EINTR);
    return result == pid;
}

static int fail(pid_t pid, const char *what) {
    perror(what);
    kill(pid, SIGKILL);
    int status;
    while (wait_child(pid, &status) && !WIFEXITED(status) && !WIFSIGNALED(status))
        ptrace(PTRACE_CONT, pid, NULL, (void *)(long)SIGKILL);
    return 2;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: bench_rss_linux report-file program [arguments...]\n");
        return 2;
    }
    pid_t pid = fork();
    if (pid < 0) { perror("fork"); return 2; }
    if (pid == 0) {
        if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) < 0) {
            perror("PTRACE_TRACEME"); _exit(125);
        }
        raise(SIGSTOP);
        execvp(argv[2], &argv[2]);
        perror("execvp");
        _exit(127);
    }
    int status;
    if (!wait_child(pid, &status) || !WIFSTOPPED(status))
        return fail(pid, "initial trace stop");
    if (ptrace(PTRACE_SETOPTIONS, pid, NULL,
               (void *)(long)(PTRACE_O_TRACEEXEC | PTRACE_O_TRACEEXIT | PTRACE_O_EXITKILL)) < 0)
        return fail(pid, "PTRACE_SETOPTIONS");
    if (ptrace(PTRACE_CONT, pid, NULL, NULL) < 0) return fail(pid, "PTRACE_CONT");

    int execs = 0, sampled = 0;
    unsigned long long peak_kib = 0;
    for (;;) {
        if (!wait_child(pid, &status)) return fail(pid, "waitpid");
        if (WIFEXITED(status) || WIFSIGNALED(status)) break;
        if (!WIFSTOPPED(status)) return fail(pid, "unexpected trace status");
        unsigned int event = (unsigned int)status >> 16;
        if (event == PTRACE_EVENT_EXEC) execs++;
        if (event == PTRACE_EVENT_EXIT && execs == 1) {
            /* VmHWM is scoped to the current mm, unlike signal->maxrss.
             * smaps_rollup also covers current resident pages when the
             * batched RSS counters under-report a very short-lived image.
             */
            unsigned long long hwm = read_kib(pid, "status", "VmHWM:");
            unsigned long long rss = read_kib(pid, "smaps_rollup", "Rss:");
            peak_kib = hwm > rss ? hwm : rss;
            sampled = peak_kib > 0;
        }
        int deliver = event ? 0 : WSTOPSIG(status);
        if (ptrace(PTRACE_CONT, pid, NULL, (void *)(long)deliver) < 0)
            return fail(pid, "PTRACE_CONT");
    }
    if (execs != 1 || !sampled) {
        fprintf(stderr, "RSS unavailable: exec-count=%d, exit-sample=%d\n", execs, sampled);
        return 2;
    }
    int rc = WIFEXITED(status) ? WEXITSTATUS(status) : -WTERMSIG(status);
    FILE *report = fopen(argv[1], "w");
    if (!report) { perror("report"); return 2; }
    fprintf(report, "%llu %d\n", peak_kib * 1024, rc);
    return fclose(report) ? 2 : 0;
}
