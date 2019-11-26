#define CATCH_CONFIG_MAIN
#include "catch.hpp"

TEST_CASE("Testing stuff")
{
    REQUIRE(10 == 10);
}

TEST_CASE("TEsting other stuff")
{
    REQUIRE(20 == 10);
}

/* 
#include <stdio.h>

int main(int argc, char **argv)
{
    printf("Hello world");
    return 0;
} */