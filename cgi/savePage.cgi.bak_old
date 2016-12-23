#!/usr/local/bin/perl -w 
use CGI; # load CGI routines
use Encode;
#use Unicode::String;
use strict;

print "Content-type: text/html\r\n\r\n";

my $q = new CGI; 

my $id=$q->param('content_id');
my $data=$q->param('data');
#$data = Encode::decode("iso-8859-1", $data);
#$data = Encode::encode("utf8", $data);
#$data = Unicode::String::latin1($data);

open F, "> /home/misha/django_app/qac/cgi/data/$id" or die "Can't open $id : $!";
print F $data;
close F;

my $link="<a href=" . '"' . "./data/$id" . '">' . "$id</>";

print $q->header, # create the HTTP header
	$q->start_html('content saved'), # start the HTML
	$q->h1("saved file $link"),  
	$q->end_html; 



