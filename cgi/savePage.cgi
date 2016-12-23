#!/usr/bin/perl 
use CGI; # load CGI routines
use strict;
use File::Path; # has a function to create all directories in the path
use Encode;

my $q = new CGI; 

my $id=$q->param('content_id');
my $data=$q->param('data');
my $wid=$q->param('wid');

my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
my $yy = int($year) + 1900;

my $dir_path =  "./serps/$yy/$mon/$mday/$wid"; 

if (-d $dir_path) {
	#no need to create new dir
}
else {
	mkpath($dir_path) or die "Cannot create dir : $!" ; # create new dir
}

#signed-in username
$data =~ s/<span id=\"gbmpn(.*?)<\/span>//;
$data =~ s/<span id=\"gbi4m1(.*?)<\/span>//;
$data =~ s/<span id=\"gbi4t(.*?)<\/span>//;
$data =~ s/<span class=\"gbps2\">(.*?)<\/span>//;

#google plus
$data =~ s/<span class=\"gbts\">(.*?)<\/span>//;


open F, "> $dir_path/$id" or die "Can't open $id : $!";
binmode F, ":utf8";
print F $data;
close F;

my $link="<a href=" . '"' . "$dir_path/$id" . '">' . "$id</>";

print $q->header, # create the HTTP header
	$q->start_html('content saved'), # start the HTML
	$q->h1("saved file $link"),  
	$q->end_html; 

