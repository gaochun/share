#! /usr/bin/perl

# Usage: Make sure you can reach checkpatch.pl at any place.
# You may set $ofono_dir to your own. 

use strict;
use Getopt::Long qw(:config no_auto_abbrev);


my $ofono_dir;
my $temp_dir;
my $check_patch_script;


my $opt_a;
my $opt_c;
my $opt_f;
my $opt_w;
my $help;
my $version = '0.1';
my $log_str = ">>check.log 2>&1";

exit Main();

################################################################################
sub Main
{
    init();

    check_apply();
    check_commit();
    check_format();    
}

sub init
{
    GetOptions(
	    'a'	        => \$opt_a,
        'c'         => \$opt_c,
        'f'         => \$opt_f,
        'w'         => \$opt_w,
	    'h|help'	=> \$help,
	    'version'	=> \$help
    ) or help(1);

    help(0) if ($help);

    if (!$opt_a && !$opt_c && !$opt_f && !$opt_w) {
        help(1);
    }
    
    if ($ofono_dir eq "") {
	    $ofono_dir = `pwd`;
        chomp($ofono_dir);
        if (!(-e "doc/ofono-paper.txt")) {
            print "Can't find a valid oFono directory!\n";
            exit;
        }
    }
    
    if ($temp_dir eq "") {
        $temp_dir = "/tmp";
    }
    
    if ($check_patch_script eq "") {
        my $kernel = `uname -r`;
        chomp($kernel);
        $check_patch_script = "/usr/src/linux-headers-$kernel/scripts/checkpatch.pl";
    }
    

    
    if ($opt_w) {
        $opt_a = 1;
        $opt_c = 1;
        $opt_f = 1;
    }
}

sub check_apply
{
    if (!$opt_a) {
        return;
    }
    
    print_start();
    
    chdir($temp_dir);
    system("rm -rf ofono");
    system("git clone git://git.kernel.org/pub/scm/network/ofono/ofono.git $log_str");

    chdir("$ofono_dir");
    system("git format-patch origin $log_str");
    
    chdir("$temp_dir/ofono");
    my $patch_files = "$ofono_dir/*.patch";
    if (system("git am $patch_files $log_str")) {
        print("Fail to apply the patch!\n");
        print_fail();
        exit;
    }
    
    # Check if oFono can build with all the patches
    if (system("./bootstrap-configure $log_str") || system("make $log_str")) {
        print("Fail to build!\n");
        print_fail();
        exit;    
    }
    
    print_succeed();
}

sub check_commit
{
    if (!$opt_c) {
        return;
    }
    
    print_start();
    
    my $error_num = 0;

    chdir($ofono_dir);
    my $status_str = `git status -s`;
    my @status_array = split("\n", $status_str);
    
    for (my $i=0; $i<=$#status_array; $i++) {
        if ($status_array[$i] !~ /patch$/ && $status_array[$i] != /check.log$/) {
            $error_num++;
        }
    }
    
    if ($error_num > 0) {
        print "$error_num files were not committed!\n";
        print "$status_str\n";
        print_fail();
    } else {
        print_succeed();
    }
}

sub check_format
{    
    if (!$opt_f) {
        return;
    }
    
    print_start();

    my $error_num = 0;

    chdir($ofono_dir);
    system("git format-patch origin $log_str");

    my @files = sort { (stat $a)[9] <=> (stat $b)[9] } glob "*.patch";
    foreach my $file (@files) {
        print "- Check basic format\n";
        if (system("$check_patch_script --no-signoff --no-tree $file $log_str") != 0) {
            $error_num++;
        }    
        
        #check the commit header and description
        print "- Check commit header and description\n";
		open FILE, $file;
		my @line_array = <FILE>;
		for (my $i = 0; $i < @line_array; $i++) {
            if ($line_array[$i] =~ /Subject: \[PATCH.*\] (.*)/) {
                my $header = $1;
                if (length($header) > 50) {
                    print "ERROR: commit header exceeds the limitation of 50 characters.\n";
                    $error_num++;   
                }            

                $i = $i + 2; # Skip the blank line
                while ($line_array[$i] !~ /---$/) {
                    if (length($line_array[$i]) > 72) {
                        print "ERROR: commit description exceeds the limitation of 72 characters per line.\nThe description is: $line_array[$i]"; 
                        $error_num++;   
                    }
                    $i++;
                }
                last;
            }        
        }
        close FILE;
    }
    
    print("- Total Errors: $error_num\n"); 
   
    if ($error_num > 0) {
        print_fail();
        exit;
    }
    
    print_succeed();
}

sub help
{
	my ($exit_code) = @_;

	print << "EOM";
Usage: $0 [OPTION]...
Version: $version

Options:
  -a                         Check if all the patches can be applied with latest code
  -c                         Check if all the changes have been committed
  -f                         Check the validity of patches
  -w                         Check all the things need to be checked               
  -h, --help, --version      Display this help and exit

EOM

	exit($exit_code);
}

sub whoami
{
    return (caller(2))[3];
}

sub print_start
{
    print "=== ".whoami()." starts ===\n";
}

sub print_fail
{
    print "=== ".whoami()." failed ===\n";
}

sub print_succeed
{
    print "=== ".whoami()." succeeded ===\n";
}

