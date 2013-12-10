#!/usr/bin/env perl

use strict;
use warnings;
use IO::Pty;
use IO::Select;
# use Term::ReadKey;

usage() if ($#ARGV < 1);

my $pty = IO::Pty->new();
my $select = IO::Select->new($pty);
my $buffer = "";

my $pid = fork();
die "Fork fail!\n" if (not defined $pid);
if ($pid != 0) {
    my $loop = 1;
    local $SIG{CHLD} = sub { $loop = 0; };
    while ($loop) {
        expect();
    }

    expect();  ##这里为什么还要一个expect，我认为是缓冲区的问题，还有就是防止子进程比父亲进程提前退出。比如passwd运行完了，那么就会丢一个信号给父进程，父进程这个时候就会退出，在expect将最后的输出打印出来之前就退出了。那么最后的输出就在屏幕上面看不到了。

                   ##查看顶上的link(chinaunix.com)
    waitpid($pid, 0);
}
else {
    my $slave = $pty->slave();
    open(STDIN, "<&", $slave);
    open(STDOUT, ">&", $slave);
    open(STDERR, ">&", $slave);
    close $pty;
    close $slave;
    exec("passwd");
    exit 1;
}

################################

sub usage {
    print STDERR "$0 Password NewPassword\n";
    exit 0;
}

sub expect {
    my ($r, $w, $e) = IO::Select->select($select, $select, undef, 0.02);
    if ($#$r > -1) {
        if (sysread($pty, my $buf, 8196)) {
            $buffer .= $buf;
            syswrite(STDOUT, $buf);
        }
    }
    else {
        return;
    }
    
    if ($#$w > -1) {
        if ($buffer =~ /\(current\) UNIX password:/) {
            $buffer = "";
            syswrite($pty, "$ARGV[0]\r");
        }
        elsif ($buffer =~ /Enter new UNIX password:/) {
            $buffer = "";
            syswrite($pty, "$ARGV[1]\r");
        }
        elsif ($buffer =~ /Retype new UNIX password:/) {
            $buffer = "";
            syswrite($pty, "$ARGV[1]\r");
        }
        else {
            ;
        }
    }
}
