#! /usr/bin/perl

# You may set $ofono_dir to your own. 

use strict;
use Getopt::Long qw(:config no_auto_abbrev);


my $ofono_dir;
my $temp_dir;
my $check_patch_script;


my $opt_a;
my $opt_c;
my $opt_d;
my $opt_f;
my $opt_w;
my $help;
my $version = '0.1';
my $log_str = ">>check.log 2>&1";
my $format_patch_str = "git format-patch -n origin $log_str";

exit Main();

################################################################################
sub Main
{
    init();

    check_apply();
    check_commit();
    set_debug_mode();
    check_format();    
}

sub init
{
    GetOptions(
	'a'			=> \$opt_a,
	'c'			=> \$opt_c,
	'd'			=> \$opt_d,
	'f'			=> \$opt_f,
	'w'			=> \$opt_w,
	'h|help'	=> \$help,
	'version'	=> \$help
    ) or help(1);

    help(0) if ($help);

    if (!$opt_a && !$opt_c && !$opt_d && !$opt_f && !$opt_w) {
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
    system("rm -f *.patch");
    system($format_patch_str);
    
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
        if ($status_array[$i] !~ /patch$/ && $status_array[$i] != /check.log$/ && $status_array[$i] != /bootstrap-configure/) {
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

sub set_debug_mode()
{
	if (!$opt_d) {
		return;
	}
	
	my $debug_mode = 0;
	my $file = "$ofono_dir/bootstrap-configure";
	
	# Check if the debug mode needs to be set.
	chdir($ofono_dir);
	open FILE, $file;
	my @line_array = <FILE>;
	my $line = $line_array[@line_array - 1];
	
	if ($line =~ /disable-optimization/) {
		$debug_mode = 1;
	}
	close FILE; 
	

    if ($opt_d == 1 && $debug_mode == 0) {
    	open FILE, ">$file";
        for (my $i = 0; $i < @line_array - 1; $i++) {
    		print FILE $line_array[$i];
    	}
    	
		chomp($line);
		print FILE $line." \\\n";
		print FILE "\t\t--disable-optimization";
	    close FILE;
	    
	    system("./bootstrap-configure");
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
    system($format_patch_str);

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

